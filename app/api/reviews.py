from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Review
from datetime import datetime
from app.util.spotify import validate_item_in_database


reviews = Blueprint("reviews", __name__)


@reviews.route("/", methods=["POST"])
@jwt_required()
def create_review():
    user_id = get_jwt_identity()
    data = request.get_json()

    rating = data.get('rating')
    comment = data.get('comment')
    is_private = data.get('isPrivate')
    spotify_id = data.get('spotifyId')
    spotify_artist_id = data.get('spotifyArtistId')

    try:
        validate_item_in_database(spotify_id, spotify_artist_id)
    except Exception as e:
        return jsonify({'message': 'error validating item in database'}), 500

    existing_review = Review.query.filter_by(user_id=user_id, spotify_id=spotify_id).first()
    if existing_review:
        return jsonify({"message": "User review for this item already exists. Use the PUT endpoint instead."}), 409

    review = Review(
        user_id=user_id,
        is_private=is_private,
        rating=rating,
        comment=comment,
        spotify_id=spotify_id,
        spotify_artist_id=spotify_artist_id
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review created successfully"}), 201


@reviews.route("/", methods=["GET"])
@jwt_required()
def get_current_user_reviews():
    """
    Fetch all reviews for the logged-in user.
    """
    user_id = get_jwt_identity()

    reviews = Review.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "id": review.id,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
            "isPrivate": review.is_private,
            "created_date": review.created_date.isoformat(),
            "updated_date": review.updated_date.isoformat(),
            "spotify_id": review.spotify_id,
            "spotify_artist_id": review.spotify_artist_id,
            "upvotes": review.upvotes,
            "downvotes": review.downvotes,
        }
        for review in reviews
    ]), 200


@reviews.route("/<int:review_id>", methods=["PUT"])
@jwt_required()
def update_review(review_id):
    user_id = get_jwt_identity()
    review = Review.query(id=review_id, user_id=user_id).first()

    if not review:
        return jsonify({"message": "No matching review found for the current user."}), 404

    data = request.get_json()

    review.rating = data.get("rating", review.rating)
    review.comment = data.get("comment", review.comment)
    review.is_private = data.get("isPrivate", review.is_private)
    review.updated_date = datetime.now()

    db.session.commit()

    return jsonify({"message": "Review updated successfully"}), 200


@reviews.route("/<int:review_id>", methods=["DELETE"])
@jwt_required()
def delete_review(review_id):
    user_id = get_jwt_identity()
    review = Review.query.get_or_404(review_id)
    if str(review.user_id) != user_id:
        return jsonify({"message": "Invalid credentials for the selected review."}), 401

    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Review deleted successfully"}), 200
