from flask import Blueprint


def register_apis(app):
    api = Blueprint('api', __name__, url_prefix='/api')

    from .auth import auth
    api.register_blueprint(auth, url_prefix='/auth')

    from .catalogs import catalogs
    api.register_blueprint(catalogs, url_prefix="/catalogs")

    from .reviews import reviews
    api.register_blueprint(reviews, url_prefix='/reviews')

    from .spotify import spotify
    api.register_blueprint(spotify, url_prefix='/spotify')

    from .user import user
    api.register_blueprint(user, url_prefix='/user')

    app.register_blueprint(api)
