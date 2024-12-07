from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # todo: update resources for different environments
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:5173"}})

    app.config.from_object('config.Config')
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    with app.app_context():
        from . import models, routes
        app.register_blueprint(routes.main)
        app.register_blueprint(routes.auth, url_prefix="/auth")
        db.create_all()

    return app
