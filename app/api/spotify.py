from flask import Blueprint, current_app, jsonify, redirect, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User
from app import db
from datetime import datetime, timedelta, timezone
import requests

spotify = Blueprint('spotify', __name__)


@spotify.route('/login', methods=['GET'])
@jwt_required()
def spotify_login():
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?response_type=code"
        f"&client_id={current_app.config['SPOTIFY_CLIENT_ID']}"
        f"&redirect_uri={current_app.config['SPOTIFY_REDIRECT_URI']}"
        f"&scope=user-read-email"
    )
    return redirect(auth_url)


@spotify.route('/callback', methods=['GET'])
@jwt_required()
def spotify_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Authorization code missing'}), 400

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

    if response.status_code != 200:
        return jsonify({'error': 'Failed to exchange code for token', 'details': token_info}), 400

    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.spotify_refresh_token = token_info.get('refresh_token')
    user.spotify_access_token = token_info.get('access_token')
    user.spotify_token_expires = datetime.now(timezone.utc) + timedelta(seconds=token_info.get('expires_in', 3600))
    db.session.commit()

    return jsonify({'message': 'Spotify tokens saved successfully'}), 200


def get_valid_access_token(user):
    if user.spotify_token_expires and datetime.now(timezone.utc) < user.spotify_token_expires:
        return user.spotify_access_token

    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': user.spotify_refresh_token,
        'client_id': current_app.config['SPOTIFY_CLIENT_ID'],
        'client_secret': current_app.config['SPOTIFY_CLIENT_SECRET'],
    }

    response = requests.post(token_url, data=token_data)
    token_info = response.json()

    if response.status_code != 200:
        raise Exception('Failed to refresh Spotify token')

    user.spotify_access_token = token_info.get('access_token')
    user.spotify_token_expires = datetime.now(timezone.utc) + timedelta(seconds=token_info.get('expires_in', 3600))
    db.session.commit()

    return user.spotify_access_token


@spotify.route('/user', methods=['GET'])
@jwt_required()
def get_user_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        access_token = get_valid_access_token(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    return response.json(), response.status_code
