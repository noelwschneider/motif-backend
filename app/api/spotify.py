from flask import Blueprint, current_app, jsonify, redirect, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Catalog, CatalogItem, Review, User
from app import db
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from sqlalchemy.sql import desc, or_
import requests
from app.util.spotify import get_user_token, get_client_token
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


@spotify.route('/user', methods=['GET'])
@jwt_required()
def get_user_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        access_token = get_user_token(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    return response.json(), response.status_code


@spotify.route('/search', methods=['GET'])
def search_spotify():
    if not request.args.get('q'):
        return jsonify({'error': 'Search query parameter "q" is required'}), 400

    # user_id = get_jwt_identity()
    # user = User.query.get(user_id)
    # if not user:
    #     return jsonify({'error': 'User not found'}), 404

    try:
        # access_token = get_spotify_access_token(user)
        access_token = get_client_token()
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
        return jsonify({'error': 'Failed to fetch search data from Spotify', 'details': response.json()}), response.status_code

    response_json = response.json()

    search_results = {
        'metadata': {
            'offset': request.args.get('offset'),
            'limit': request.args.get('limit'),
            'q': request.args.get('q'),
            'type': request.args.get('q'),
            'count': {
                'albums': response_json.get('albums', {}).get('total'),
                'artists': response_json.get('artists', {}).get('total'),
                'tracks': response_json.get('tracks', {}).get('total'),
            }
        },
        'albums': [],
        'artists': [],
        'tracks': [],
    }

    for album in response_json.get('albums', {}).get('items', []):
        artists_list = []
        for artist in album.get('artists', []):
            artist_obj = {
                "spotifyId": artist.get('id'),
                "title": artist.get('name'),
            }
            artists_list.append(artist_obj)

        album_obj = {
            'spotifyId': album.get('id'),
            'title': album.get('name'),
            'images': album.get('images', []),
            'releaseDate': album.get('release_date'),
            'tracksCount': album.get('total_tracks'),
            'albumType': album.get('album_type'),
            'artists': artists_list
        }
        search_results['albums'].append(album_obj)

    for artist in response_json.get('artists', {}).get('items', []):
        artist_obj = {
            'spotifyId': artist.get('id'),
            'title': artist.get('name'),
            'images': artist.get('images'),
            'popularity': artist.get('popularity'),
            'genres': artist.get('genres', [])
        }
        search_results['artists'].append(artist_obj)

    for track in response_json.get('tracks', {}).get('items', []):
        album = track.get('album', {})
        artists_list = []
        for artist in track.get('artists', []):
            artist_obj = {
                "spotifyId": artist.get('id'),
                "title": artist.get('name'),
            }
            artists_list.append(artist_obj)

        track_obj = {
            'spotifyId': track.get('id'),
            'title': track.get('name'),
            'durationMs': track.get('duration_ms'),
            'popularity': track.get('popularity'),
            'images': album.get('images', []),
            'releaseDate': album.get('release_date'),
            'album': {
                'title': album.get('name'),
                'spotifyId': album.get('id'),
                'albumType': album.get('album_type')
            },
            'artists': artists_list
        }
        search_results['tracks'].append(track_obj)

    return jsonify(search_results), 200


@spotify.route('/artist-profile', methods=['GET'])
@jwt_required(optional=True)
def fetch_artist_albums():
    user_id = get_jwt_identity()

    if not request.args.get('id'):
        return jsonify({'error': 'Artist ID parameter "id" is required'}), 400
    spotify_artist_id = request.args.get('id')

    try:
        access_token = get_client_token()
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    # reviews
    sorted_reviews_query = (
        Review.query.filter_by(
            spotify_artist_id=spotify_artist_id,
            is_private=False
        ).order_by(
            # case((Review.user_id == user_id, 1), else_=0).desc(),
            desc(Review.upvotes),
            desc(Review.created_date)
        )
    )
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
    reviews_dict = dict(reviews)

    sorted_catalogs_query = (
        db.session.query(
            CatalogItem.id.label("catalog_item_id"),
            CatalogItem.spotify_id.label("catalog_item_spotify_id"),
            Catalog.id.label("catalog_id"),
            Catalog.user_id,
            Catalog.upvotes,
            Catalog.downvotes,
            Catalog.created_date,
            Catalog.updated_date,
            Catalog.comment,
            Catalog.image_url,
            Catalog.name,
        )
        .join(Catalog, CatalogItem.catalog_id == Catalog.id)
        .filter(
            CatalogItem.spotify_artist_id == spotify_artist_id,
            or_(Catalog.is_private == False, (user_id is not None and Catalog.user_id == user_id))
        )
        .order_by(
            desc(Catalog.upvotes),
            desc(Catalog.created_date)
        )
    )
    catalogs = defaultdict(list)
    for catalog in sorted_catalogs_query:
        catalogs[catalog.catalog_item_spotify_id].append({
            "catalogItemId": catalog.catalog_item_id,
            "catalogItemSpotifyId": catalog.catalog_item_spotify_id,
            "catalogId": catalog.catalog_id,
            "user_id": catalog.user_id,
            "upvotes": catalog.upvotes,
            "downvotes": catalog.downvotes,
            "createdDate": catalog.created_date,
            "updatedDate": catalog.updated_date,
            "comment": catalog.comment,
            "image_url": catalog.image_url,
            "name": catalog.name
        })

    catalogs_dict = dict(catalogs)

    # artist data
    response = requests.get(
        f'https://api.spotify.com/v1/artists/{request.args.get('id')}',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch artist data from Spotify', 'details': response.json()}), response.status_code
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
        return jsonify({'error': 'Failed to fetch artist albums data from Spotify', 'details': response.json()}), response.status_code
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
    album_id_str = album_id_str[:-1]
    # todo: prepare multiple requests if items > 20
    if album_id_str:
        response = requests.get(
            'https://api.spotify.com/v1/albums',
            headers={'Authorization': f'Bearer {access_token}'},
            params={
                'ids': album_id_str,
                'market': 'US'
            }
        )

        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch albums data from Spotify', 'details': response.json()}), response.status_code
        else:
            albums_response = response.json()
    else:
        albums_response = {'albums': []}

    albums = []
    for album in albums_response.get('albums', []):
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
        "reviews": reviews_dict,
        "catalogs": catalogs_dict
    }

    return jsonify(artist_profile), 200
