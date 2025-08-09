# ==== MENSAJES CENTRALIZADOS ====
MENSAJES = {
    "agradecimiento": (
        "Gracias por avisarnos.\n"
        "Lamentamos que no puedas asistir esta vez, pero esperamos verte en futuras dinámicas.\n"
        "¡Gracias por tu apoyo al reciclar y sumar con nosotros! ♻️✨"
    ),
    "ayuda": (
        "No logramos procesar tu respuesta. Te pedimos seleccionar una de las opciones posibles. "
        "Si tienes dudas o necesitas ayuda adicional, puedes:\n"
        "📧 Escribirnos a: info@correo.com.mx\n"
        "📞 Llamarnos al: 55 5555 5555"
    ),
    "MSG_PEDIR_FECHA_TITULO": (
        "Te pedimos que por favor nos confirmes la fecha de asistencia para tus boletos dentro de las 3 opciones posibles.\n"
        "Ten en cuenta lo siguiente:\n"
        "✅ Es necesario recibir tu confirmación completa en un lapso de 24 horas para poder hacer válida la promoción. Tenemos un cupo limitado por fecha y la asignación se hará por orden de confirmación.\n"
        "✅ La fecha seleccionada no estará sujeta a cambios.\n"
        "✅ Deberás recoger los boletos previamente en nuestras oficinas."
    ),
    "MSG_NOMBRE_CONFIRM_TEXTO": (
        "¡Gracias! Deberás presentar una identificación oficial para hacerte la entrega de tus boletos. "
        "Por favor, confírmanos que el nombre registrado es correcto:\n"
        "[Nombre completo en la lista]"
    ),
    "MSG_FINAL": (
        "¡Excelente! La fecha asignada para tus cupones es el domingo [Fecha elegida] con el nombre [Nombre confirmado].\n"
        "Te confirmamos que ya te encuentras en lista de invitados. 🎉\n"
        "Podrás recoger tus boletos a partir de miércoles 13 de agosto\n"
        "🕗 Horario:\n"
        "Lunes a viernes: 8:00 a.m. a 7:00 p.m.\n"
        "Sábados: 10:00 a.m. a 2:00 p.m.\n"
        "ℹ️Ten en cuenta lo siguiente para tu acceso al museo::\n"
        "​​🚪El ingreso se realizará por Jardín de Grupos, reja azul ubicada a un costado del museo, únicamente a personas que presenten un cupón físico con la firma y sello de Papalote Museo del Niño. No se permitirá el ingreso a personas sin cupón.\n"
        "🔎No se aceptarán duplicados, alteraciones ni cupones fuera de vigencia.\n"
        "🎟️Cada cupón es personal y será canjeado por un brazalete que servirá como comprobante de ingreso. \n"
        "📅El cupón es válido únicamente para el día especificado y solo incluye el acceso al museo. El acceso al Domo será con costo adicional.\n"
        "⏰El horario de ingreso es a partir de las 10:00 a.m. y hasta el horario de cierre de taquilla o hasta completar el aforo máximo del Museo.\n"
        "🍔 No se permitirá ingresar con comida ni bebidas.\n"
        "🎒No podrás ingresar con mochilas o bolsos grandes ya que no hay espacio de paquetería o resguardo.\n"
        "♻️Sabemos tu interés en reciclar y en favor del medio ambiente, pero en esta ocasión ya no contaremos con recolección de PET en el museo. \n"
        "¡Te esperamos y gracias por participar ! 🎶✨"
    ),
    "SIN_DISPONIBILIDAD_EN_FECHA": (
        "Gracias por tu interés. 😔\n"
        "Lamentablemente, la disponibilidad de los boletos para el domingo [fecha elegida] ya se ha agotado.\n"
        "Te pedimos por favor elegir entre una de las siguientes fechas que aún tienen disponibilidad:\n"
        "[Fecha alternativa 1]\n"
        "[Fecha alternativa 2]\n"
        "Ya no me interesan los boletos"
    ),
    "CONFIRMACION_NOMBRE": (
        "Por favor, escribe tu nombre completo como aparece en tu identificación oficial, "
        "para poder hacer la corrección en la lista y asegurar tu lugar correctamente."
    )
}

def render_msg(key: str, **vars):
    """Reemplaza placeholders tipo [Fecha elegida] en el mensaje."""
    txt = MENSAJES[key]
    for k, v in vars.items():
        txt = txt.replace(f"[{k}]", str(v))
    return txt
