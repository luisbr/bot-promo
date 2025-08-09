from flask import Blueprint, jsonify
bp = Blueprint("health", __name__)

@bp.route("/", methods=["GET"])
def home():
    return jsonify({"status":"running"})
