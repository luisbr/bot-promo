from flask import Flask
import logging
from config import init_config
from routes.webhook import bp as webhook_bp
from routes.health import bp as health_bp

def create_app():
    init_config()
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.register_blueprint(webhook_bp)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
