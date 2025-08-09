import os
import logging
from dotenv import load_dotenv

def init_config():
    load_dotenv('/etc/whatsapp-bot.env')
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

class Settings:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "secret")
    DB_NAME = os.getenv("DB_NAME", "botdb")
    VONAGE_WA_NUMBER = os.getenv("VONAGE_WA_NUMBER")
    VONAGE_AUTH = os.getenv("VONAGE_AUTH")
    TEMPLATE_INICIAL = os.getenv("TEMPLATE_INICIAL", "confirmacion_evento_pet")
    TEMPLATE_LANG = os.getenv("TEMPLATE_LANG", "es")
    MSG_AGRADECIMIENTO_NO = os.getenv("MSG_AGRADECIMIENTO_NO", "Gracias por tu respuesta. ¡Hasta pronto!")
    MSG_AYUDA = os.getenv("MSG_AYUDA", "Este canal solo atiende confirmaciones. Usa los botones o responde lo solicitado.")
    MSG_PEDIR_FECHA_TITULO = os.getenv("MSG_PEDIR_FECHA_TITULO", "Selecciona tu fecha:")
    MSG_NOMBRE_CONFIRM_TEXTO = os.getenv("MSG_NOMBRE_CONFIRM_TEXTO", "Confirma tu nombre: {nombre}")
    MSG_FINAL = os.getenv("MSG_FINAL", "¡Listo {nombre}! Te esperamos el {fecha}.")
    BTN_SI = os.getenv("BTN_SI", "Sí")
    BTN_NO = os.getenv("BTN_NO", "No")
    BTN_YA_NO = os.getenv("BTN_YA_NO", "Ya no me interesa")
    FECHA_1 = os.getenv("FECHA_1", "Domingo 17 agosto 2025")
    FECHA_2 = os.getenv("FECHA_2", "Domingo 24 agosto 2025")
    FECHA_3 = os.getenv("FECHA_3", "Domingo 31 agosto 2025")
    USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
