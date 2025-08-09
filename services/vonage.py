import requests, logging
from config import Settings

log = logging.getLogger("vonage")
BASE_URL = "https://api.nexmo.com/v0.1/messages"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {Settings.VONAGE_AUTH}"
}

def send_text(to_number: str, body: str):
    payload = {
        "from": {"type": "whatsapp", "number": Settings.VONAGE_WA_NUMBER},
        "to":   {"type": "whatsapp", "number": to_number},
        "message": {"content": {"type": "text", "text": body}}
    }
    r = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=20)
    log.info("send_text %s -> %s %s", to_number, r.status_code, r.text[:200])
    return r.status_code, r.text

def send_template_inicial(to_number: str, nombre: str):
    payload = {
        "from": {"type":"whatsapp","number": Settings.VONAGE_WA_NUMBER},
        "to":   {"type":"whatsapp","number": to_number},
        "message": {
            "template": {
                "name": Settings.TEMPLATE_INICIAL,
                "language": {"code": Settings.TEMPLATE_LANG},
                "components": [{
                    "type": "body",
                    "parameters": [{"type":"text","text": nombre or ""}]
                }]
            }
        }
    }
    r = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=20)
    log.info("send_template %s -> %s %s", to_number, r.status_code, r.text[:200])
    return r.status_code, r.text

def send_buttons_freeform(to_number: str, title: str, options):
    buttons = [{"type":"reply","reply":{"id": oid, "title": otitle}} for oid, otitle in options][:3]
    payload = {
        "from": {"type":"whatsapp","number": Settings.VONAGE_WA_NUMBER},
        "to":   {"type":"whatsapp","number": to_number},
        "message": {
            "content": {
                "type": "custom",
                "custom": {
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": title},
                        "action": {"buttons": buttons}
                    }
                }
            }
        }
    }
    r = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=20)
    log.info("send_buttons %s -> %s %s", to_number, r.status_code, r.text[:200])
    return r.status_code, r.text
