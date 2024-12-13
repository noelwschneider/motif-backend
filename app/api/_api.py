from flask import Blueprint


def register_apis(app):
    from .auth import auth
    from .spotify import spotify

    api = Blueprint('api', __name__, url_prefix='/api')
    api.register_blueprint(auth, url_prefix='/auth')
    api.register_blueprint(spotify, url_prefix='/spotify')

    app.register_blueprint(api)
