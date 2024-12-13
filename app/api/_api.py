from flask import Blueprint


def register_apis(app):
    from .auth import auth

    api = Blueprint('api', __name__, url_prefix='/api')
    api.register_blueprint(auth, url_prefix='/auth')

    app.register_blueprint(api)
