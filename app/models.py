from . import db
from datetime import datetime, timezone
from enum import Enum


# class CatalogItemType(Enum):
#     ALBUM = 'album'
#     ARTIST = 'artist'
#     SONG = 'song'


class MusicItemType(Enum):
    ALBUM = 'album'
    ARTIST = 'artist'
    TRACK = 'track'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(80), unique=True, nullable=True)
    profile_pic_url = db.Column(db.String(256), nullable=True)
    spotify_refresh_token = db.Column(db.String(512), nullable=True)
    spotify_access_token = db.Column(db.String(512), nullable=True)
    spotify_token_expires = db.Column(
        db.DateTime(timezone=True),
        nullable=True)


class Album(db.Model):
    __tablename__ = 'albums'

    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(128), unique=True, nullable=True, index=True)
    title = db.Column(db.String(120), nullable=False)
    upc = db.Column(db.String(30), unique=True, nullable=True)

    album_type = db.Column(
        db.Enum("album", "single", "compilation", name="album_type_enum"),
        nullable=False)
    duration_ms = db.Column(db.Integer, nullable=True)
    total_tracks = db.Column(db.Integer, nullable=True)
    release_date = db.Column(db.Date, nullable=True)
    explicit = db.Column(db.Boolean, nullable=True)
    label = db.Column(db.String(120), nullable=True)

    image_url_640px = db.Column(db.String(512), nullable=True)
    image_url_300px = db.Column(db.String(512), nullable=True)
    image_url_64px = db.Column(db.String(512), nullable=True)


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(128), unique=True, nullable=True, index=True)
    title = db.Column(db.String(120), nullable=False)

    image_url_640px = db.Column(db.String(512), nullable=True)
    image_url_320px = db.Column(db.String(512), nullable=True)
    image_url_160px = db.Column(db.String(512), nullable=True)


class Catalog(db.Model):
    __tablename__ = 'catalogs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    private = db.Column(db.Boolean, default=False, nullable=False)

    created_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False)
    updated_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref='catalogs', lazy=True)
    items = db.relationship('CatalogItem',
                            back_populates='catalog',
                            cascade='all, delete-orphan')


class CatalogItem(db.Model):
    __tablename__ = 'catalog_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    catalog_id = db.Column(
        db.Integer,
        db.ForeignKey('catalogs.id', ondelete='CASCADE'),
        nullable=False)

    item_id = db.Column(
        db.Integer,
        nullable=False)
    item_type = db.Column(db.Enum(MusicItemType, name="music_item_type_enum"), nullable=False)
    spotify_id = db.Column(db.String(128), nullable=True)
    spotify_artist_id = db.Column(db.String(128), nullable=True)
    position = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.Text, nullable=True)

    created_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False)

    catalog = db.relationship('Catalog', back_populates='items')


# todo: track user review history over time
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spotify_id = db.Column(db.String(128), nullable=False)
    spotify_artist_id = db.Column(db.String(128), db.ForeignKey('artists.spotify_id'), nullable=False)
    created_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False)
    updated_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    is_private = db.Column(db.Boolean, default=True)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)


class Track(db.Model):
    __tablename__ = 'tracks'

    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(128), unique=True, nullable=True, index=True)
    isrc = db.Column(db.String(30), unique=True, nullable=True)
    iswc = db.Column(db.String(30), unique=True, nullable=True)

    title = db.Column(db.String(120), nullable=False)
    disc_number = db.Column(db.Integer, nullable=True)
    track_order = db.Column(db.Integer, nullable=True)

    duration = db.Column(db.Integer, nullable=True)
    explicit = db.Column(db.Boolean, nullable=True)


class ArtistAlbumTrack(db.Model):
    __tablename__ = 'artist_album_track'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), nullable=True)
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), nullable=True)
    spotify_id = db.Column(db.String(128), unique=True, nullable=True, index=True)
