from flask_jwt_extended import create_access_token, create_refresh_token, get_csrf_token


def set_user_cookies(response, identity):
    new_access_token = create_access_token(identity=identity)
    new_refresh_token = create_refresh_token(identity=identity)

    response.set_cookie('access_token_cookie', new_access_token, httponly=True, secure=True, samesite='None')
    response.set_cookie('refresh_token_cookie', new_refresh_token, httponly=True, secure=True, samesite='None')
    response.set_cookie('csrf_access_token', get_csrf_token(new_access_token), samesite='None', secure=True)
    response.set_cookie('csrf_refresh_token', get_csrf_token(new_refresh_token), samesite='None', secure=True)

    return response
