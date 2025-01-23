from flask import Blueprint, current_app, jsonify, redirect, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Review, User
from app import db
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from sqlalchemy import case, desc
import requests

spotify = Blueprint('spotify', __name__)


# todo:
# use public token for search/artist-profile endpoints
# clean up fetch_artist_albums

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


@spotify.route('/search', methods=['GET'])
@jwt_required()
def search_spotify():
    if not request.args.get('q'):
        return jsonify({'error': 'Search query parameter "q" is required'}), 400

    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        access_token = get_valid_access_token(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    response = requests.get(
        'https://api.spotify.com/v1/search',
        headers={'Authorization': f'Bearer {access_token}'},
        params={
            'q': request.args.get('q'),
            'type': request.args.get('type'),
            'limit': int(request.args.get('limit')),
            'offset': int(request.args.get('offset')),
        }
    )

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Spotify', 'details': response.json()}), response.status_code

    return jsonify(response.json()), 200


@spotify.route('/artist-profile', methods=['GET'])
@jwt_required()
def fetch_artist_albums():
    if not request.args.get('id'):
        return jsonify({'error': 'Artist ID parameter "id" is required'}), 400
    spotify_artist_id = request.args.get('id')

    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        access_token = get_valid_access_token(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    # reviews
    sorted_reviews_query = (
        Review.query.filter_by(spotify_artist_id=spotify_artist_id, private=False)
        .order_by(
            case((Review.user_id == user_id, 1), else_=0).desc(),
            desc(Review.upvotes),
            desc(Review.created_date)
        )
    )
    print('\n')
    print('after reviews query')
    reviews = defaultdict(list)
    for review in sorted_reviews_query:
        reviews[review.spotify_id].append({
            "spotifyId": review.spotify_id,
            "reviewId": review.id,
            "userId": review.user_id,
            "comment": review.comment,
            "rating": review.rating,
            "createdDate": review.created_date,
            "upvotes": review.upvotes,
        })
    print('after dict iteration')
    reviews_dict = dict(reviews)
    print('after reviews dict')
    print('\n')

    # artist data
    response = requests.get(
        f'https://api.spotify.com/v1/artists/{request.args.get('id')}',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Spotify', 'details': response.json()}), response.status_code
    else:
        artist_response = response.json()

    # artist albums
    response = requests.get(
        f'https://api.spotify.com/v1/artists/{request.args.get('id')}/albums',
        headers={'Authorization': f'Bearer {access_token}'},
        params={
            'include_groups': 'album',
            'market': 'US',
            'limit': 50,
            'offset': 0
        }
    )
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Spotify', 'details': response.json()}), response.status_code
    else:
        artist_albums_response = response.json()

    # albums (w/ track data)
    album_id_str = ''
    count = 0
    for item in artist_albums_response.get("items", []):
        if count >= 20:
            break
        count += 1
        album_id_str += f'{item.get('id')},'
    response = requests.get(
        'https://api.spotify.com/v1/albums',
        headers={'Authorization': f'Bearer {access_token}'},
        params={
            'ids': album_id_str,
            'market': 'US'
        }
    )

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Spotify', 'details': response.json()}), response.status_code
    else:
        albums_response = response.json()
    albums = []
    for album in albums_response.get('albums'):
        tracks = []
        for track in album.get('tracks', {}).get('items', []):
            tracks.append({
                'title': track.get('name'),
                'spotifyId': track.get('id'),
                'durationMs': track.get('duration_ms'),
                'discNumber': track.get('disc_number'),
                'trackNumber': track.get('track_number'),
                'explicit': track.get('explicit'),
                'isPlayable': track.get('is_playable')
            })
        albums.append({
            'title': album.get('name'),
            'spotifyId': album.get('id'),
            'releaseDate': album.get('release_date'),
            'popularity': album.get('popularity'),
            'images': album.get('images'),
            'tracks': tracks
        })

    artist_profile = {
        'title': artist_response.get('name'),
        'popularity': artist_response.get('popularity'),
        'spotifyId': artist_response.get('id'),
        'images': artist_response.get('images'),
        "albums": albums,
        "reviews": reviews_dict
    }

    return jsonify(artist_profile), 200
