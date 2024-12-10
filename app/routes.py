from flask import Blueprint, current_app, jsonify, make_response, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, verify_jwt_in_request
from .models import User, db
import requests

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return jsonify({'message': 'Flask backend is running!'})


auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    response = make_response(jsonify({'message': 'Login successful'}), 200)

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    # todo: environment-based cookie config
    # samesite = 'None' if current_app.config['ENV'] == 'development' else 'Lax'
    # secure = False if current_app.config['ENV'] == 'development' else True
    # response.set_cookie('access_token', access_token, httponly=True, secure=secure, samesite=samesite)
    # response.set_cookie('refresh_token', refresh_token, httponly=True, secure=secure, samesite=samesite)

    response.set_cookie('access_token_cookie', access_token, httponly=True, secure=True, samesite='None')
    response.set_cookie('refresh_token_cookie', refresh_token, httponly=True, secure=True, samesite='None')
    return response


@auth.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
    response.set_cookie('access_token_cookie', '', httponly=True, secure=True, samesite='Lax', expires=0)
    response.set_cookie('refresh_token_cookie', '', httponly=True, secure=True, samesite='Lax', expires=0)
    return response


@auth.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    new_refresh_token = create_refresh_token(identity=current_user)

    response = jsonify({'message': 'Token refreshed'})
    response.set_cookie('access_token_cookie', new_access_token, httponly=True, secure=True, samesite='Lax')
    response.set_cookie('refresh_token_cookie', new_refresh_token, httponly=True, secure=True, samesite='None')
    return response


@auth.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    try:
        verify_jwt_in_request(optional=False)
        current_user = get_jwt_identity()
        return jsonify({'message': f'Welcome, {current_user["username"]}!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 401


@auth.route('/verify', methods=['GET'])
@jwt_required()
def verify():
    current_user = get_jwt_identity()
    return jsonify({'authenticated': True, 'user': current_user}), 200


@auth.route('/spotify-login', methods=['GET'])
def spotify_login():
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?response_type=code"
        f"&client_id={current_app.config['SPOTIFY_CLIENT_ID']}"
        f"&redirect_uri={current_app.config['SPOTIFY_REDIRECT_URI']}"
        f"&scope=user-read-email"
    )
    return jsonify({'auth_url': auth_url}), 200


@auth.route('/callback', methods=['GET'])
def spotify_callback():
    code = request.args.get('code')

    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': current_app.config['SPOTIFY_REDIRECT_URI'],
        'client_id': current_app.config['SPOTIFY_CLIENT_ID'],
        'client_secret': current_app.config['SPOTIFY_CLIENT_SECRET'],
    }
    response = requests.post(token_url, data=token_data)
    token_info = response.json()

    return jsonify({'token_info': token_info}), 200
