# envio.py
import os, sys, json, time, requests, mysql.connector
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('.env')  # ajusta ruta si usas otro .env

DB_CFG = dict(
    host=os.getenv("DB_HOST","localhost"),
    user=os.getenv("DB_USER","root"),
    password=os.getenv("DB_PASS","secret"),
    database=os.getenv("DB_NAME","botdb"),
)

VONAGE_WA_NUMBER = os.getenv("VONAGE_WA_NUMBER")
VONAGE_AUTH      = os.getenv("VONAGE_AUTH")  # Base64(API_KEY:API_SECRET)
TEMPLATE_NAME    = os.getenv("TEMPLATE_INICIAL","confirmacion_evento_pet")
LANG_CODE        = os.getenv("TEMPLATE_LANG","es")

LIMIT_USUARIOS   = int(os.getenv("BATCH_MAX_USERS","240"))
LIMIT_BOLETOS    = int(os.getenv("BATCH_MAX_TICKETS","1000"))
DRY_RUN          = os.getenv("DRY_RUN","false").lower() == "true"

def db():
    return mysql.connector.connect(**DB_CFG)

def pick_candidates(conn):
    """
    Tomamos más de 240 y filtramos en Python acumulando hasta ≤1000 boletos.
    Prioriza por id asc (ajusta si quieres otra prioridad).
    """
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, telefono, nombre, boletos
        FROM usuarios
        WHERE estado='START'
        ORDER BY id ASC
        LIMIT 1000
    """)
    rows = cur.fetchall()
    cur.close()

    lote, total_boletos = [], 0
    for r in rows:
        if len(lote) >= LIMIT_USUARIOS:
            break
        if total_boletos + r["boletos"] > LIMIT_BOLETOS:
            break
        lote.append(r)
        total_boletos += r["boletos"]
    return lote, total_boletos

def send_template_inicial(telefono:str, nombre:str):
    url = "https://api.nexmo.com/v0.1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {VONAGE_AUTH}",
    }
    payload = {
        "from": {"type":"whatsapp","number": VONAGE_WA_NUMBER},
        "to":   {"type":"whatsapp","number": telefono},
        "message": {
            "template": {
                "name": TEMPLATE_NAME,
                "language": {"code": LANG_CODE},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type":"text","text": nombre or ""}  # {{1}} = nombre
                        ]
                    }
                ]
            }
        }
    }
    if DRY_RUN:
        print("[DRY_RUN] Enviaría plantilla a", telefono, "payload:", json.dumps(payload, ensure_ascii=False))
        return 200, "DRY_RUN"

    r = requests.post(url, json=payload, headers=headers, timeout=20)
    return r.status_code, r.text

def mark_sent(conn, usuario_id:int, telefono:str, payload_json:dict, http_status:int, http_body:str):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.cursor()
    # avanzar estado + guardar última plantilla + fecha_contacto
    cur.execute("""
        UPDATE usuarios
           SET estado='PLANTILLA_INICIAL',
               ultima_plantilla=%s,
               fecha_contacto=%s,
               updated_at=%s
         WHERE id=%s
    """, (TEMPLATE_NAME, now, now, usuario_id))

    # log
    cur.execute("""
        INSERT INTO logs (usuario_id, telefono, tipo, canal, contenido)
        VALUES (%s, %s, 'saliente', 'whatsapp', %s)
    """, (usuario_id, telefono, json.dumps({
        "action": "send_template_inicial",
        "template": TEMPLATE_NAME,
        "http_status": http_status,
        "http_body": http_body,
        "payload": payload_json
    })))
    conn.commit()
    cur.close()

def main():
    print("== Envío diario: límite usuarios:", LIMIT_USUARIOS, "límite boletos:", LIMIT_BOLETOS, "DRY_RUN:", DRY_RUN)
    conn = db()
    try:
        candidatos, total_boletos = pick_candidates(conn)
        if not candidatos:
            print("No hay usuarios en estado START.")
            return

        print(f"Seleccionados {len(candidatos)} usuarios, suma boletos={total_boletos}")
        enviados = 0
        for u in candidatos:
            status, body = send_template_inicial(u["telefono"], u["nombre"])
            print(f"[{status}] {u['telefono']} -> {body[:200]}")
            try:
                payload_preview = {"telefono": u["telefono"], "nombre": u["nombre"]}
                mark_sent(conn, u["id"], u["telefono"], payload_preview, status, body)
                enviados += 1
            except Exception as e:
                print("Error al marcar/loguear en DB:", e)
            # opcional: pequeño sleep para no saturar
            time.sleep(0.05)

        print(f"Envío terminado. Total enviados={enviados}.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
