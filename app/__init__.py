from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # Allow cross-origin requests

    # Placeholder for future configuration
    app.config.from_object('config.Config')

    # Placeholder for Blueprints
    with app.app_context():
        from .routes import main
        app.register_blueprint(main)

    return app
