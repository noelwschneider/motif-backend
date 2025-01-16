from flask import Blueprint


def register_apis(app):
    api = Blueprint('api', __name__, url_prefix='/api')

    from .auth import auth
    api.register_blueprint(auth, url_prefix='/auth')

    from .catalogs import catalogs
    api.register_blueprint(catalogs, url_prefix="/catalogs")

    from .spotify import spotify
    api.register_blueprint(spotify, url_prefix='/spotify')

    app.register_blueprint(api)
