from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, ArtistAlbumTrack, Artist, Album, Track, Catalog, CatalogItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc
from datetime import datetime
from app.util.spotify import validate_item_in_database


catalogs = Blueprint("catalogs", __name__)


@catalogs.route("/", methods=["POST"])
@jwt_required()
def create_catalog():
    # todo: prevent duplicate catalog names
    user_id = get_jwt_identity()
    data = request.get_json()

    name = data.get("name")
    comment = data.get("comment", "")
    is_private = data.get("isPrivate", False)
    image_url = data.get("imageUrl")

    if not name:
        return jsonify({"error": "Catalog name is required"}), 400

    catalog = Catalog(
        user_id=user_id,
        name=name,
        comment=comment,
        is_private=is_private,
        image_url=image_url
    )

    db.session.add(catalog)
    db.session.commit()

    return jsonify({"message": "Catalog created successfully", "id": catalog.id}), 201


@catalogs.route("/user", methods=["GET"])
@jwt_required()
def get_current_user_catalogs():
    user_id = get_jwt_identity()

    catalogs = Catalog.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "id": catalog.id,
            "name": catalog.name,
            "comment": catalog.comment,
            "isPrivate": catalog.is_private,
            "imageUrl": catalog.image_url,
            "created_date": catalog.created_date.isoformat(),
            "updated_date": catalog.updated_date.isoformat(),
        }
        for catalog in catalogs
    ]), 200


@catalogs.route("/<int:catalog_id>", methods=["GET"])
@jwt_required(optional=True)
def get_catalog(catalog_id):
    user_id = get_jwt_identity()
    catalog = Catalog.query.filter_by(id=catalog_id).first()
    if not catalog:
        return jsonify({ "message": "Catalog not found"})

    if (catalog.is_private and catalog.user_id != user_id):
        return jsonify({ "message": "User does not have permission to view this catalog."}), 403

    catalog_items_query = CatalogItem.query.with_entities(
        CatalogItem.id.label("catalog_item_id"),
        CatalogItem.spotify_id.label("catalog_item_spotify_id"),
        CatalogItem.position,
        CatalogItem.comment,
        CatalogItem.created_date,
        CatalogItem.updated_date,
        Artist.id.label("artist_id"),
        Artist.spotify_id.label("artist_spotify_id"),
        Artist.title.label("artist_title"),
        Artist.image_url_640px.label("artist_image_url_640px"),
        Artist.image_url_320px.label("artist_image_url_320px"),
        Artist.image_url_160px.label("artist_image_url_160px"),
        Album.id.label("album_id"),
        Album.spotify_id.label("album_spotify_id"),
        Album.title.label("album_title"),
        Album.album_type,
        Album.total_tracks,
        Album.release_date,
        Album.image_url_640px.label("album_image_url_640px"),
        Album.image_url_300px.label("album_image_url_300px"),
        Album.image_url_64px.label("album_image_url_64px"),
        Track.id.label("track_id"),
        Track.spotify_id.label("track_spotify_id"),
        Track.title.label("track_title"),
        Track.disc_number,
        Track.track_order,
        Track.duration_ms,
        Track.explicit,
    ).join(
        ArtistAlbumTrack, CatalogItem.spotify_id == ArtistAlbumTrack.spotify_id
    ).join(
        Artist, ArtistAlbumTrack.artist_id == Artist.id
    ).outerjoin(
        Album, ArtistAlbumTrack.album_id == Album.id
    ).outerjoin(
        Track, ArtistAlbumTrack.track_id == Track.id
    ).filter(
        CatalogItem.catalog_id == catalog_id
    ).order_by(
        asc(CatalogItem.position),
        asc(CatalogItem.created_date)
    ).all()

    catalog_items = [
        {
            "id": row.catalog_item_id,
            "spotify_id": row.catalog_item_spotify_id,
            "position": row.position,
            "comment": row.comment,
            "created_date": row.created_date,
            "updated_date": row.updated_date,
            "artist": {
                "id": row.artist_id,
                "spotify_id": row.artist_spotify_id,
                "title": row.artist_title,
                "image_url_640px": row.artist_image_url_640px,
                "image_url_320px": row.artist_image_url_320px,
                "image_url_160px": row.artist_image_url_160px,
            },
            "album": None if row.album_id is None else {
                "id": row.album_id,
                "spotify_id": row.album_spotify_id,
                "title": row.album_title,
                "album_type": row.album_type,
                "total_tracks": row.total_tracks,
                "release_date": row.release_date,
                "image_url_640px": row.album_image_url_640px,
                "image_url_300px": row.album_image_url_300px,
                "image_url_64px": row.album_image_url_64px,
            },
            "track": None if row.track_id is None else {
                "id": row.track_id,
                "spotify_id": row.track_spotify_id,
                "title": row.track_title,
                "disc_number": row.disc_number,
                "track_order": row.track_order,
                "duration_ms": row.duration_ms,
                "explicit": row.explicit,
            }
        }
        for row in catalog_items_query
    ]

    return jsonify({
        "id": catalog.id,
        "name": catalog.name,
        "comment": catalog.comment,
        "isPrivate": catalog.is_private,
        "created_date": catalog.created_date.isoformat(),
        "updated_date": catalog.updated_date.isoformat(),
        "items": catalog_items
    }), 200


@catalogs.route("/user/<int:user_id>", methods=["GET"])
def get_user_public_catalogs(user_id):
    catalogs = Catalog.query.filter_by(user_id=user_id, is_private=False).all()

    return jsonify([
        {
            "id": catalog.id,
            "name": catalog.name,
            "comment": catalog.comment,
            "isPrivate": catalog.is_private,
            "imageUrl": catalog.image_url,
            "created_date": catalog.created_date.isoformat(),
            "updated_date": catalog.updated_date.isoformat(),
        }
        for catalog in catalogs
    ]), 200


@catalogs.route("/<int:catalog_id>", methods=["PUT"])
@jwt_required()
def update_catalog(catalog_id):
    user_id = get_jwt_identity()
    catalog = Catalog.query.filter_by(id=catalog_id, user_id=user_id).first()
    if not catalog:
        return jsonify({"message": "No matching catalog found for the current user."}), 404

    data = request.get_json()

    catalog.name = data.get("name", catalog.name)
    catalog.comment = data.get("comment", catalog.comment)
    catalog.is_private = data.get("isPrivate", catalog.is_private)
    catalog.image_url = data.get("imageUrl", catalog.image_url)
    catalog.updated_date = datetime.now()

    db.session.commit()

    return jsonify({"message": "Catalog updated successfully"}), 200


@catalogs.route("/<int:catalog_id>", methods=["DELETE"])
@jwt_required()
def delete_catalog(catalog_id):
    user_id = get_jwt_identity()
    catalog = Catalog.query.filter_by(id=catalog_id, user_id=user_id).first()
    if not catalog:
        return jsonify({"message": "No matching catalog found for the current user."}), 404

    db.session.delete(catalog)
    db.session.commit()

    return jsonify({"message": "Catalog deleted successfully"}), 200


@catalogs.route("/<int:catalog_id>", methods=["POST"])
@jwt_required()
def add_item_to_catalog(catalog_id):
    user_id = get_jwt_identity()
    catalog = Catalog.query.filter_by(id=catalog_id, user_id=user_id).first()
    if not catalog:
        return jsonify({"message": "No matching catalog found for the current user."}), 404

    data = request.get_json()
    spotify_id = data.get('spotifyId')
    spotify_artist_id = data.get('spotifyArtistId')
    position = data.get('position')
    comment = data.get('comment')

    if not spotify_id or not spotify_artist_id:
        return jsonify({ "message": "request most include spotifyId and spotifyArtistId properties"}), 400

    validate_item_in_database(spotify_id, spotify_artist_id)

    try:
        item = CatalogItem(
            catalog_id=catalog.id,
            spotify_id=spotify_id,
            spotify_artist_id=spotify_artist_id,
            position=position,
            comment=comment
        )
        db.session.add(item)
        db.session.commit()
    except ValueError:
        return jsonify({"error": "Invalid item_type"}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Item already exists in this catalog"}), 409

    return jsonify({"message": "Item added to catalog", "item_id": item.id}), 201


@catalogs.route("/item/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_catalog_item(item_id):
    user_id = get_jwt_identity()

    item = CatalogItem.query.join(
            Catalog, CatalogItem.catalog_id == Catalog.id
        ).filter(
            CatalogItem.id == item_id,
            Catalog.user_id == user_id
        ).first()

    if not item:
        return jsonify({"message": "No matching catalog found for the current user."}), 404

    data = request.get_json()

    item.position = data.get("position", item.position)
    item.comment = data.get("comment", item.comment)

    db.session.commit()

    return jsonify({"message": "Catalog updated successfully"}), 200


@catalogs.route("/item/<int:item_id>", methods=["DELETE"])
@jwt_required()
def remove_item_from_catalog(item_id):
    user_id = get_jwt_identity()
    item = CatalogItem.query.join(
        Catalog, CatalogItem.catalog_id == Catalog.id
    ).filter(
        CatalogItem.id == item_id,
        Catalog.user_id == user_id
    ).first()

    if not item:
        return jsonify({"message": "No matching item found for the current user."}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Item removed from catalog"}), 200
