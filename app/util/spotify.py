from flask import current_app
from app.models import User, Artist, Album, Track, ArtistAlbumTrack
from app import db
from datetime import datetime, timedelta, timezone
import base64
import requests


SPOTIFY_API_URL = 'https://api.spotify.com/v1'


def get_user_token(user):
    if user.spotify_token_expires and datetime.now(timezone.utc) < user.spotify_token_expires:
        return user.spotify_access_token

    token_url = 'https://accounts.spotify.com/api/token'
    client_id = current_app.config['SPOTIFY_CLIENT_ID']
    client_secret = current_app.config['SPOTIFY_CLIENT_SECRET']

    if user.id == -1:
        token_data = {
            'grant_type': 'client_credentials',
        }
        auth_str = base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8'))
        auth_str = auth_str.decode('utf-8')
        headers = {
            'Authorization': f'Basic {auth_str}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    else:
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': user.spotify_refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
        }
        headers = {}

    response = requests.post(token_url, data=token_data, headers=headers)
    token_info = response.json()

    if response.status_code != 200:
        raise Exception('Failed to refresh Spotify token')

    user.spotify_access_token = token_info.get('access_token')
    user.spotify_token_expires = datetime.now(timezone.utc) + timedelta(seconds=token_info.get('expires_in', 3600))
    db.session.commit()

    return user.spotify_access_token


def get_client_token():
    user = User.query.get(-1)
    access_token = get_user_token(user)
    return access_token


def validate_item_in_database(spotify_id, spotify_artist_id):
    try:
        access_token = get_client_token()

        artist_row = Artist.query.filter_by(spotify_id=spotify_artist_id).first()
        if not artist_row:
            response = requests.get(
                f'https://api.spotify.com/v1/artists/{spotify_artist_id}',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            artist_json = response.json()
            artist_row = Artist(
                spotify_id=spotify_artist_id,
                image_url_640px=artist_json.get('images', [])[0].get('url'),
                image_url_320px=artist_json.get('images', [])[1].get('url'),
                image_url_160px=artist_json.get('images', [])[2].get('url'),
                title=artist_json.get('name'),
            )
            db.session.add(artist_row)
            db.session.commit()

            artist_join_row = ArtistAlbumTrack(
                artist_id=artist_row.id,
                album_id=None,
                track_id=None,
                spotify_id=spotify_artist_id
            )
            db.session.add(artist_join_row)
            db.session.commit()

        artist_album_track = ArtistAlbumTrack.query.filter_by(
            artist_id=artist_row.id,
            spotify_id=spotify_id
        ).first()

        if artist_album_track:
            return True

        album_response = requests.get(
            f'https://api.spotify.com/v1/albums/{spotify_id}',
            headers={'Authorization': f'Bearer {access_token}'},
            params={'market': 'US'}
        )
        if album_response.status_code == 200:
            track_json = None
            album_json = album_response.json()
        else:
            track_response = requests.get(
                f'https://api.spotify.com/v1/tracks/{spotify_id}',
                headers={'Authorization': f'Bearer {access_token}'},
                params={'market': 'US'}
            )
            if track_response.status_code == 200:
                track_json = track_response.json()
                album_json = track_json.get('album')

        if not album_json:
            return False

        album_row = Album.query.filter_by(spotify_id=album_json.get('id')).first()
        if not album_row:
            album_row = Album(
                spotify_id=album_json.get('id'),
                image_url_640px=album_json.get('images', [])[0].get('url'),
                image_url_300px=album_json.get('images', [])[0].get('url'),
                image_url_64px=album_json.get('images', [])[0].get('url'),
                title=album_json.get('name'),
                total_tracks=album_json.get('total_tracks'),
                release_date=album_json.get('release_date'),
                album_type=album_json.get('album_type')
            )
            db.session.add(album_row)
            db.session.commit()

            album_join_row = ArtistAlbumTrack(
                artist_id=artist_row.id,
                album_id=album_row.id,
                track_id=None,
                spotify_id=album_json.get('id')
            )
            db.session.add(album_join_row)
            db.session.commit()

        if not track_json:
            return True

        track_row = Track.query.filter_by(spotify_id=track_json.get('id')).first()
        if not track_row:
            track_row = Track(
                title=track_json.get('name'),
                track_order=track_json.get('track_number'),
                duration_ms=track_json.get('duration_ms'),
                explicit=track_json.get('explicit'),
                spotify_id=track_json.get('id'),
                disc_number=track_json.get('disc_number'),
            )
            db.session.add(track_row)
            db.session.commit()

            track_join_row = ArtistAlbumTrack(
                artist_id=artist_row.id,
                album_id=album_row.id,
                track_id=track_row.id,
                spotify_id=track_json.get('id')
            )
            db.session.add(track_join_row)
            db.session.commit()

        return True

    except Exception as e:
        return False
