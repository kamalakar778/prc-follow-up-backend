from flask import Flask
from app.routes.document_routes import document_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(document_bp)
    return app
