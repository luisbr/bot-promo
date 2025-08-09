from flask import Blueprint, request, jsonify
import logging, json
from utils.whatsapp_parser import parse_inbound
from services.flow import handle_inbound

bp = Blueprint("webhook", __name__)
log = logging.getLogger("webhook")

@bp.route("/webhook/inbound", methods=["POST"])
def inbound():
    data = request.get_json(silent=True) or {}
    log.info("[WEBHOOK DATA] %s", json.dumps(data, ensure_ascii=False))
    parsed = parse_inbound(data)
    log.info("[PARSED] %s", parsed)
    handle_inbound(parsed["user_number"], parsed["text"], parsed["choice"])
    return jsonify({"status":"ok"})
