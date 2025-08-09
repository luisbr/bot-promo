# routes/webhook.py
from flask import Blueprint, request, jsonify, current_app as app
import json, os
from datetime import datetime

# importamos utilidades del proyecto
from services.vonage import send_text
from messages import MENSAJES
import mysql.connector

bp = Blueprint("webhook", __name__)

FECHAS_VALIDAS = {"1 SEP","2 SEP","3 SEP"}

def db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST","localhost"),
        user=os.getenv("DB_USER","root"),
        password=os.getenv("DB_PASS","secret"),
        database=os.getenv("DB_NAME","botdb")
    )

def parse_inbound(data: dict):
    content = (data.get("message") or {}).get("content") or {}
    text, choice = None, None

    # Vonage "reply" al nivel raíz (cuando pulsa botón quick-reply)
    if not choice and data.get("message_type") == "reply":
        rep = data.get("reply") or {}
        choice = rep.get("id") or rep.get("title")

    # Texto normal
    if not text and content.get("type") == "text":
        text = content.get("text")

    # Botón normalizado
    if not choice and content.get("type") == "button":
        btn = content.get("button", {}) or {}
        choice = btn.get("payload") or btn.get("text")

    # Botón “custom” raw (interactive)
    if not choice:
        custom = content.get("custom") or {}
        interactive = custom.get("interactive") or {}
        btn_reply = interactive.get("button_reply") or {}
        choice = btn_reply.get("id") or btn_reply.get("title")

    # Alterno
    if not text:
        text = content.get("text") or data.get("text")

    # Remitente
    sender = (data.get("from") or {})
    if isinstance(sender, dict):
        tel = sender.get("number") or sender.get("id")
    else:
        tel = str(sender)

    return tel, text, choice

def normaliza_si_no(s):
    if not s: return None
    t = s.strip().lower()
    if t in ("si","sí","s","yes","y"): return "SI"
    if t in ("no","n"): return "NO"
    return None

def normaliza_fecha(x):
    if not x: return None
    t = x.strip().upper()
    if t in FECHAS_VALIDAS: return t
    m = (t.replace("OPCION","").replace("OPCIÓN","").replace("OP","").strip())
    if m in ("1","UNO","PRIMERO"): return "1 SEP"
    if m in ("2","DOS","SEGUNDO"): return "2 SEP"
    if m in ("3","TRES","TERCERO"): return "3 SEP"
    return None

def nombre_valido(s):
    if not s: return False
    s = s.strip()
    if len(s) < 2 or len(s) > 80: return False
    if any(ch.isdigit() for ch in s): return False
    if "http" in s.lower(): return False
    return True

def get_row(cr, tel):
    cr.execute("SELECT * FROM usuarios WHERE telefono=%s", (tel,))
    return cr.fetchone()

def ensure_user(cr, tel):
    row = get_row(cr, tel)
    if not row:
        cr.execute("INSERT INTO usuarios (telefono, estado, intentos) VALUES (%s,%s,%s)", (tel, "START", 0))
        return {"telefono": tel, "estado": "START", "intentos": 0}
    return row

def set_fields(cr, tel, **kv):
    if not kv: return
    sets = ", ".join(f"{k}=%s" for k in kv.keys())
    vals = list(kv.values()) + [tel]
    cr.execute(f"UPDATE usuarios SET {sets} WHERE telefono=%s", vals)

@bp.route("/webhook/inbound", methods=["POST"])
def inbound():
    data = request.get_json(silent=True) or {}
    app.logger.info("[WEBHOOK DATA] %s", json.dumps(data, ensure_ascii=False))

    tel, text, choice = parse_inbound(data)
    app.logger.info("[FROM]%s [TEXT]%s [CHOICE]%s", tel, text, choice)

    cn = db()
    cr = cn.cursor(dictionary=True)

    user = ensure_user(cr, tel)
    estado = user.get("estado","START")
    intentos = user.get("intentos", 0)
    fecha_elegida = user.get("fecha_confirmada")
    nombre = user.get("nombre")

    # START → pedir fecha
    if estado == "START":
        set_fields(cr, tel, estado="ELEGIR_FECHA", intentos=0, fecha_respuesta=datetime.now())
        cn.commit()
        send_text(tel, MENSAJES["MSG_PEDIR_FECHA_TITULO"])
        return jsonify({"status":"ok","next":"ELEGIR_FECHA"})

    # ELEGIR_FECHA
    if estado == "ELEGIR_FECHA":
        fecha = normaliza_fecha(choice or text)
        if not fecha:
            intentos += 1
            set_fields(cr, tel, intentos=intentos, fecha_respuesta=datetime.now())
            cn.commit()
            send_text(tel, MENSAJES["ayuda"])
            return jsonify({"status":"ok","error":"fecha_invalida","intentos":intentos})
        set_fields(cr, tel,
                   estado="CONFIRMACION_FINAL",
                   fecha_confirmada=fecha,
                   intencion="confirmar",
                   intentos=0,
                   fecha_respuesta=datetime.now())
        cn.commit()
        send_text(tel, f"Has elegido {fecha}. ¿Confirmas tu asistencia? Responde 'sí' o 'no'.")
        return jsonify({"status":"ok","fecha":fecha,"next":"CONFIRMACION_FINAL"})

    # CONFIRMACION_FINAL
    if estado == "CONFIRMACION_FINAL":
        sn = normaliza_si_no(text or "")
        if not sn:
            intentos += 1
            set_fields(cr, tel, intentos=intentos, fecha_respuesta=datetime.now())
            cn.commit()
            send_text(tel, "Por favor responde 'sí' o 'no'.")
            return jsonify({"status":"ok","error":"sn_invalido","intentos":intentos})
        if sn == "NO":
            set_fields(cr, tel, estado="CERRADO", confirmado=False, intencion="rechazar", fecha_respuesta=datetime.now())
            cn.commit()
            send_text(tel, MENSAJES["agradecimiento"])
            return jsonify({"status":"ok","confirmado":False,"next":"CERRADO"})
        # SI
        set_fields(cr, tel, estado="CAPTURAR_NOMBRE", confirmado=True, intentos=0, fecha_respuesta=datetime.now())
        cn.commit()
        send_text(tel, MENSAJES["CONFIRMACION_NOMBRE"])
        return jsonify({"status":"ok","confirmado":True,"next":"CAPTURAR_NOMBRE"})

    # CAPTURAR_NOMBRE
    if estado == "CAPTURAR_NOMBRE":
        if not nombre_valido(text or ""):
            intentos += 1
            set_fields(cr, tel, intentos=intentos, fecha_respuesta=datetime.now())
            cn.commit()
            send_text(tel, "No detecté un nombre válido. Ejemplo: 'Juan Pérez'. Inténtalo de nuevo.")
            return jsonify({"status":"ok","error":"nombre_invalido","intentos":intentos})
        nombre_ok = text.strip()
        fecha_final = fecha_elegida or "1 SEP"
        set_fields(cr, tel, estado="CERRADO", nombre=nombre_ok, intentos=0, fecha_respuesta=datetime.now())
        cn.commit()
        final_txt = MENSAJES["MSG_FINAL"].replace("[Fecha elegida]", fecha_final).replace("[Nombre confirmado]", nombre_ok)
        send_text(tel, final_txt)
        return jsonify({"status":"ok","nombre":nombre_ok,"next":"CERRADO"})

    # CERRADO (o desconocido)
    send_text(tel, "Tu registro ya fue procesado. Si necesitas ayuda, responde a este mensaje.")
    cn.commit()
    cr.close(); cn.close()
    return jsonify({"status":"ok","fin":True})
