from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object('config.Config')
    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        from . import models, routes
        app.register_blueprint(routes.main)
        app.register_blueprint(routes.auth)
        db.create_all()

    return app
