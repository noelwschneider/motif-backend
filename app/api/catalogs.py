from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Catalog, CatalogItem, MusicItemType
from sqlalchemy.exc import IntegrityError
from datetime import datetime

catalogs = Blueprint("catalogs", __name__)


@catalogs.route("/", methods=["POST"])
@jwt_required()
def create_catalog():
    """
    Create a new catalog for the logged-in user.
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    name = data.get("name")
    description = data.get("description", "")
    private = data.get("private", False)

    if not name:
        return jsonify({"error": "Catalog name is required"}), 400

    catalog = Catalog(
        user_id=user_id,
        name=name,
        description=description,
        private=private
    )

    db.session.add(catalog)
    db.session.commit()

    return jsonify({"message": "Catalog created successfully", "id": catalog.id}), 201


@catalogs.route("/", methods=["GET"])
@jwt_required()
def get_user_catalogs():
    """
    Fetch all catalogs for the logged-in user.
    """
    user_id = get_jwt_identity()

    catalogs = Catalog.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "id": catalog.id,
            "name": catalog.name,
            "description": catalog.description,
            "private": catalog.private,
            "created_date": catalog.created_date.isoformat(),
            "updated_date": catalog.updated_date.isoformat(),
        }
        for catalog in catalogs
    ]), 200


@catalogs.route("/<int:catalog_id>", methods=["GET"])
@jwt_required()
def get_catalog(catalog_id):
    """
    Get details for a specific catalog.
    """
    catalog = Catalog.query.get_or_404(catalog_id)

    return jsonify({
        "id": catalog.id,
        "name": catalog.name,
        "description": catalog.description,
        "private": catalog.private,
        "created_date": catalog.created_date.isoformat(),
        "updated_date": catalog.updated_date.isoformat(),
        "items": [
            {
                "id": item.id,
                "item_id": item.item_id,
                "item_type": item.item_type.value,
                "date_added": item.date_added.isoformat(),
                "position": item.position,
                "notes": item.notes
            }
            for item in catalog.items
        ]
    }), 200


@catalogs.route("/<int:catalog_id>", methods=["PUT"])
@jwt_required()
def update_catalog(catalog_id):
    """
    Update an existing catalog.
    """
    catalog = Catalog.query.get_or_404(catalog_id)
    data = request.get_json()

    catalog.name = data.get("name", catalog.name)
    catalog.description = data.get("description", catalog.description)
    catalog.private = data.get("private", catalog.private)
    catalog.updated_date = datetime.now()

    db.session.commit()

    return jsonify({"message": "Catalog updated successfully"}), 200


@catalogs.route("/<int:catalog_id>", methods=["DELETE"])
@jwt_required()
def delete_catalog(catalog_id):
    """
    Delete a catalog and its associated items.
    """
    catalog = Catalog.query.get_or_404(catalog_id)

    db.session.delete(catalog)
    db.session.commit()

    return jsonify({"message": "Catalog deleted successfully"}), 200


# todo: trigger side effect for checking/populating related rows in artists, albums, tracks, and artist_album_track tables
@catalogs.route("/<int:catalog_id>/items", methods=["POST"])
@jwt_required()
def add_item_to_catalog(catalog_id):
    """
    Add an item to a specific catalog.
    """
    catalog = Catalog.query.get_or_404(catalog_id)
    data = request.get_json()

    item_id = data.get("item_id")
    item_type = data.get("item_type")
    position = data.get("position")
    notes = data.get("notes")

    if not item_id or not item_type:
        return jsonify({"error": "item_id and item_type are required"}), 400


    try:
        item = CatalogItem(
            catalog_id=catalog.id,
            item_id=item_id,
            item_type=MusicItemType(item_type),
            position=position,
            notes=notes
        )
        db.session.add(item)
        db.session.commit()
    except ValueError:
        return jsonify({"error": "Invalid item_type"}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Item already exists in this catalog"}), 409

    return jsonify({"message": "Item added to catalog", "item_id": item.id}), 201


@catalogs.route("/<int:catalog_id>/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
def remove_item_from_catalog(catalog_id, item_id):
    """
    Remove an item from a catalog.
    """
    item = CatalogItem.query.filter_by(catalog_id=catalog_id, id=item_id).first_or_404()

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Item removed from catalog"}), 200
