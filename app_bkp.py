from flask import Flask, request, jsonify
import openai
import os
import requests
import mysql.connector
from datetime import datetime
import json
import re
import time

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

def call_openai_json(prompt):
    """
    Llama a OpenAI y devuelve (intencion, fecha).
    Reintentos, log de respuesta cruda y parseo robusto de JSON.
    """
    for attempt in range(3):
        try:
            res = openai.ChatCompletion.create(
                model="gpt-4",  # ajusta si usas otro modelo
                messages=[
                    {"role": "system", "content": (
                        "Eres un asistente que SOLO devuelve JSON válido. "
                        "Nunca agregues texto fuera del JSON."
                    )},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            raw = res.choices[0].message["content"]
            print("[GPT][raw]:", raw)  # Log crudo

            # 1) Intento directo
            try:
                g = json.loads(raw)
                return g.get("intencion", "desconocido"), g.get("fecha")
            except Exception:
                pass

            # 2) Extraer objeto JSON con regex si vino con ruido
            m = re.search(r'\{[\s\S]*\}', raw)
            if m:
                maybe_json = m.group(0)
                try:
                    g = json.loads(maybe_json)
                    return g.get("intencion", "desconocido"), g.get("fecha")
                except Exception:
                    print("[GPT] JSON extraído pero no parseable.")

            print("[GPT] No se pudo parsear JSON, intento", attempt+1)
        except Exception as e:
            print("[GPT] Error en request:", e)
        time.sleep(0.5)

    return "desconocido", None

def send_whatsapp(to_number, text):
    payload = {
        "from": {"type": "whatsapp", "number": os.getenv("VONAGE_WA_NUMBER")},
        "to": {"type": "whatsapp", "number": to_number},
        "message": {"content": {"type": "text", "text": text}}
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {os.getenv('VONAGE_AUTH')}"
    }
    r = requests.post("https://api.nexmo.com/v0.1/messages", json=payload, headers=headers)
    print("[Vonage] Resp:", r.status_code, r.text[:300])

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "secret"),
        database=os.getenv("DB_NAME", "botdb")
    )

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "running"})

@app.route("/webhook/inbound", methods=["POST"])
def inbound():
    data = request.get_json(silent=True) or {}

    # Log payload crudo
    try:
        print("[Inbound] Payload:", json.dumps(data, ensure_ascii=False))
    except Exception:
        print("[Inbound] Payload no serializable")

    # Extraer texto y número de forma tolerante
    msg_text = (data.get("message") or {}).get("content", {}).get("text")
    if not msg_text:
        msg_text = data.get("text") or (data.get("message") or {}).get("text")

    sender = (data.get("from") or data.get("sender") or {})
    user_number = None
    if isinstance(sender, dict):
        user_number = sender.get("number") or sender.get("id")
    if not user_number:
        user_number = data.get("from_number") or data.get("msisdn") or data.get("from")

    if not msg_text or not user_number:
        print("[Inbound] Faltan datos clave (texto/número)")
        return jsonify({"status": "ignored"}), 200

    # Conectar DB
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # UPSERT usuario
    cursor.execute("SELECT id FROM usuarios WHERE telefono = %s", (user_number,))
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO usuarios (telefono, fecha_respuesta, respuesta_original) VALUES (%s, NOW(), %s)",
            (user_number, msg_text)
        )
        conn.commit()

    # Prompt para intención/fecha
    prompt = f"""
Interpreta la respuesta del usuario para confirmar asistencia a un evento.
Fechas válidas: "1 SEP", "2 SEP", "3 SEP".

Mensaje del usuario:
\"\"\"{msg_text}\"\"\"

Responde SOLO en JSON EXACTO:
{{
  "intencion": "confirmar" | "rechazar" | "desconocido",
  "fecha": "1 SEP" | "2 SEP" | "3 SEP" | null
}}
- Si el usuario dice que NO asiste, usa "rechazar" y fecha null.
- Si confirma pero no especifica claramente, devuelve "desconocido" y fecha null.
- Acepta variantes: "el primero", "opción 2", "voy el 3", "1", "2", "3", "uno", "dos", "tres".
"""
    intencion, fecha = call_openai_json(prompt)
    print(f"[GPT][parsed] intencion={intencion}, fecha={fecha}")

    # Guardar resultado
    cursor.execute("""
        UPDATE usuarios
        SET respuesta_original = %s,
            intencion = %s,
            fecha_confirmada = %s,
            fecha_respuesta = NOW(),
            confirmado = %s
        WHERE telefono = %s
    """, (msg_text, intencion, fecha, intencion == "confirmar", user_number))
    conn.commit()
    cursor.close()
    conn.close()

    # Respuesta por WhatsApp
    if intencion == "confirmar" and fecha:
        reply = f"¡Gracias! Has elegido asistir el {fecha}. Puedes recoger tu boleto en Plaza Central, Local 3, entre 10am y 5pm."
    elif intencion == "rechazar":
        reply = "Gracias por avisarnos. Esperamos verte en otro evento próximamente."
    else:
        reply = "Este número solo está destinado para confirmar tu fecha de asistencia al evento. Por favor responde con: 1 SEP, 2 SEP, 3 SEP o NO VOY."

    send_whatsapp(user_number, reply)
    return jsonify({"status": "ok"}), 200
