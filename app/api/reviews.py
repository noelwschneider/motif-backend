from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Review
from datetime import datetime

reviews = Blueprint("reviews", __name__)


@reviews.route("/", methods=["POST"])
@jwt_required()
def create_review():
    user_id = get_jwt_identity()
    data = request.get_json()

    item_id = data.get('item_id')
    item_type = data.get('item_type')
    rating = data.get('rating')
    comment = data.get('comment')
    private = data.get('private')
    artist_id = data.get('artist_id')

    review = Review(
        user_id=user_id,
        item_id=item_id,
        item_type=item_type,
        artist_id=artist_id,
        private=private,
        rating=rating,
        comment=comment
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review created successfully"}), 201


@reviews.route("/", methods=["GET"])
@jwt_required()
def get_user_reviews():
    """
    Fetch all reviews for the logged-in user.
    """
    user_id = get_jwt_identity()

    reviews = Review.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "id": review.id,
            "item_id": review.item_id,
            "item_type": review.item_type,
            "artist_id": review.artist_id,
            "rating": review.rating,
            "comment": review.comment,
            "private": review.private,
            "created_date": review.created_date.isoformat(),
            "updated_date": review.updated_date.isoformat()
        }
        for review in reviews
    ]), 200


# todo: get all reviews for an artist (+ their albums/tracks)
@reviews.route("/artist/<int:artist_id>", methods=["GET"])
def get_artist_reviews(artist_id):
    reviews = Review.query.filter_by(artist_id=artist_id, private=False).all()
    # todo: create artist/album/track hierarchy
    return jsonify([
        {
            "id": review.id,
            "item_id": review.item_id,
            "item_type": review.item_type,
            "artist_id": review.artist_id,
            "rating": review.rating,
            "comment": review.comment,
            "private": review.private,
            "created_date": review.created_date.isoformat(),
            "updated_date": review.updated_date.isoformat()
        }
        for review in reviews
    ]), 200


@reviews.route("/<int:review_id>", methods=["PUT"])
@jwt_required()
def update_review(review_id):
    """
    Update an existing review.
    """
    review = Review.query.get_or_404(review_id)
    data = request.get_json()

    review.rating = data.get("rating", review.rating)
    review.comment = data.get("comment", review.comment)
    review.private = data.get("private", review.private)
    review.updated_date = datetime.now()

    db.session.commit()

    return jsonify({"message": "Review updated successfully"}), 200


@reviews.route("/<int:review_id>", methods=["DELETE"])
@jwt_required()
def delete_review(review_id):
    """
    Delete a review
    """
    review = Review.query.get_or_404(review_id)

    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Review deleted successfully"}), 200
