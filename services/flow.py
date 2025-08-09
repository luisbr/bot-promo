import logging
from config import Settings
from db import get_conn
from services.vonage import send_text, send_buttons_freeform

log = logging.getLogger("flow")

def get_user_by_phone(conn, tel):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM usuarios WHERE telefono=%s", (tel,))
    row = cur.fetchone()
    cur.close()
    return row

def set_user_state(conn, uid, **fields):
    if not fields: return
    sets = ", ".join(f"{k}=%s" for k in fields.keys())
    vals = list(fields.values()) + [uid]
    cur = conn.cursor()
    cur.execute(f"UPDATE usuarios SET {sets} WHERE id=%s", vals)
    conn.commit()
    cur.close()

def eventos_disponibles_para(conn, boletos):
    cur = conn.cursor(dictionary=True)
    cur.execute("""        SELECT id, nombre_publico, fecha, cupo_total, boletos_ocupados,
               (cupo_total - boletos_ocupados) AS cupo_disponible
        FROM eventos
        WHERE activo = TRUE AND (cupo_total - boletos_ocupados) >= %s
        ORDER BY fecha ASC
    """, (boletos,))
    rows = cur.fetchall()
    cur.close()
    return rows

def reservar_cupo(conn, evento_id, boletos):
    cur = conn.cursor()
    cur.execute("""        UPDATE eventos
        SET boletos_ocupados = boletos_ocupados + %s
        WHERE id = %s AND (cupo_total - boletos_ocupados) >= %s
    """, (boletos, evento_id, boletos))
    ok = cur.rowcount == 1
    conn.commit()
    cur.close()
    return ok

def handle_inbound(user_number, text, choice):
    conn = get_conn()
    try:
        user = get_user_by_phone(conn, user_number)
        if not user:
            send_text(user_number, "No encontramos tu registro.")
            return

        estado = user["estado"]
        boletos = user["boletos"] or 1

        if estado == "START":
            send_text(user_number, Settings.MSG_AYUDA)
            return

        if estado == "PLANTILLA_INICIAL":
            if choice and choice.strip().lower() in [Settings.BTN_SI.lower(), "si", "sí"]:
                disponibles = eventos_disponibles_para(conn, boletos)
                opciones = []
                for ev in disponibles:
                    if ev["nombre_publico"] in [Settings.FECHA_1, Settings.FECHA_2, Settings.FECHA_3]:
                        opciones.append((f"EVT_{ev['id']}", ev["nombre_publico"]))
                if not opciones:
                    send_text(user_number, "Por ahora no hay cupo disponible. Intenta más tarde.")
                    return
                if len(opciones) == 2:
                    opciones.append(("YA_NO", Settings.BTN_YA_NO))
                send_buttons_freeform(user_number, Settings.MSG_PEDIR_FECHA_TITULO, opciones[:3])
                set_user_state(conn, user["id"], estado="ELEGIR_FECHA")
                return
            elif choice and choice.strip().lower() in [Settings.BTN_NO.lower(), "no"]:
                send_text(user_number, Settings.MSG_AGRADECIMIENTO_NO)
                set_user_state(conn, user["id"], estado="RECHAZADO")
                return
            else:
                send_text(user_number, Settings.MSG_AYUDA)
                return

        if estado == "ELEGIR_FECHA":
            if not choice:
                send_text(user_number, Settings.MSG_AYUDA)
                return
            up = choice.strip().upper()
            if up == "YA_NO":
                send_text(user_number, Settings.MSG_AGRADECIMIENTO_NO)
                set_user_state(conn, user["id"], estado="RECHAZADO")
                return
            if up.startswith("EVT_"):
                try:
                    evento_id = int(up.split("_",1)[1])
                except Exception:
                    send_text(user_number, Settings.MSG_AYUDA)
                    return
                if reservar_cupo(conn, evento_id, boletos):
                    set_user_state(conn, user["id"], evento_id=evento_id, estado="NOMBRE_CONFIRMAR")
                    send_buttons_freeform(
                        user_number,
                        Settings.MSG_NOMBRE_CONFIRM_TEXTO.format(nombre=user.get("nombre") or ""),
                        [("NOMBRE_OK","Sí, es correcto"), ("NOMBRE_EDIT","No, favor de corregir nombre")]
                    )
                else:
                    disponibles = eventos_disponibles_para(conn, boletos)
                    opciones = [(f"EVT_{ev['id']}", ev["nombre_publico"]) for ev in disponibles]
                    if not opciones:
                        send_text(user_number, "La fecha elegida ya no tiene cupo y no hay otras con espacio disponible.")
                        return
                    send_buttons_freeform(user_number, "Esa fecha se llenó. Elige otra:", opciones[:3])
                return
            send_text(user_number, Settings.MSG_AYUDA)
            return

        if estado == "NOMBRE_CONFIRMAR":
            if choice and choice.upper() == "NOMBRE_OK":
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT nombre_publico FROM eventos WHERE id=%s", (user["evento_id"],))
                ev = cur.fetchone()
                cur.close()
                fecha_pub = ev["nombre_publico"] if ev else "tu fecha"
                nombre = user.get("nombre_confirmado") or user.get("nombre") or ""
                send_text(user_number, Settings.MSG_FINAL.format(nombre=nombre, fecha=fecha_pub))
                set_user_state(conn, user["id"], estado="CONFIRMADO")
                return
            elif choice and choice.upper() == "NOMBRE_EDIT":
                send_text(user_number, "Por favor, escribe tu nombre completo como debe aparecer.")
                set_user_state(conn, user["id"], estado="NOMBRE_CORREGIR")
                return
            else:
                send_text(user_number, Settings.MSG_AYUDA)
                return

        if estado == "NOMBRE_CORREGIR":
            if not text:
                send_text(user_number, "Escribe tu nombre para continuar.")
                return
            nombre = text.strip()
            if len(nombre) < 2 or not any(c.isalpha() for c in nombre):
                send_text(user_number, "No detecté un nombre válido. Ejemplo: Juan Pérez")
                return
            set_user_state(conn, user["id"], nombre_confirmado=nombre, nombre=nombre, estado="NOMBRE_CONFIRMAR")
            send_buttons_freeform(
                user_number,
                Settings.MSG_NOMBRE_CONFIRM_TEXTO.format(nombre=nombre),
                [("NOMBRE_OK","Sí, es correcto"), ("NOMBRE_EDIT","No, favor de corregir nombre")]
            )
            return

        send_text(user_number, Settings.MSG_AYUDA)
    finally:
        conn.close()
