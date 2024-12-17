from . import db


track_artist = db.Table(
    'track_artist',
    db.Column('track_id', db.Integer, db.ForeignKey('tracks.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    spotify_refresh_token = db.Column(db.String(512), nullable=True)
    spotify_access_token = db.Column(db.String(512), nullable=True)
    spotify_token_expires = db.Column(db.DateTime(timezone=True), nullable=True)


class Album(db.Model):
    __tablename__ = 'albums'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    duration_ms = db.Column(db.Integer, nullable=True)
    explicit = db.Column(db.Boolean, nullable=True)
    label = db.Column(db.String(120), nullable=True)
    isrc = db.Column(db.String(30), unique=True, nullable=True)
    upc = db.Column(db.String(30), unique=True, nullable=True)
    ean = db.Column(db.String(30), unique=True, nullable=True)
    album_type = db.Column(db.Enum("album", "single", "compilation", name="album_type_enum"), nullable=False)
    spotify_id = db.Column(db.String(128), unique=True, nullable=True)
    image_url_640px = db.Column(db.String(512), nullable=True)
    image_url_300px = db.Column(db.String(512), nullable=True)
    image_url_64px = db.Column(db.String(512), nullable=True)

    tracks = db.relationship('Track', back_populates='album', cascade="all, delete-orphan")


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    spotify_id = db.Column(db.String(128), unique=True, nullable=True)
    image_url_640px = db.Column(db.String(512), nullable=True)
    image_url_320px = db.Column(db.String(512), nullable=True)
    image_url_160px = db.Column(db.String(512), nullable=True)

    tracks = db.relationship('Track', secondary=track_artist, back_populates='artists')


class Track(db.Model):
    __tablename__ = 'tracks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    track_order = db.Column(db.Integer, nullable=True)
    isrc = db.Column(db.String(30), unique=True, nullable=True)
    ean = db.Column(db.String(30), unique=True, nullable=True)
    upc = db.Column(db.String(30), unique=True, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    explicit = db.Column(db.Boolean, nullable=True)
    spotify_id = db.Column(db.String(128), unique=True, nullable=True)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), nullable=False)

    album = db.relationship('Album', back_populates='tracks')
    artists = db.relationship('Artist', secondary=track_artist, back_populates='tracks')


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=True)


class List(db.Model):
    __tablename__ = 'lists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
