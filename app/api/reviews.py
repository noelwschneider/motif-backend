from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Review, User
from datetime import datetime
from app.util.spotify import validate_item_in_database
from collections import defaultdict
from sqlalchemy.sql import desc


reviews = Blueprint("reviews", __name__)


# todo: upvote / downvote functionality


@reviews.route("/", methods=["POST"])
@jwt_required()
def create_review():
    user_id = get_jwt_identity()
    data = request.get_json()

    comment = data.get('comment')
    is_private = data.get('isPrivate')
    rating = data.get('rating')
    spotify_artist_id = data.get('spotifyArtistId')
    spotify_id = data.get('spotifyId')

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
    user_id = get_jwt_identity()

    reviews = Review.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "comment": review.comment,
            "createdDate": review.created_date.isoformat(),
            "downvotes": review.downvotes,
            "id": review.id,
            "isPrivate": review.is_private,
            "rating": review.rating,
            "spotifyArtistId": review.spotify_artist_id,
            "spotifyId": review.spotify_id,
            "updatedDate": review.updated_date.isoformat(),
            "upvotes": review.upvotes,
            "userId": review.user_id,
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


# todo: join on user table for user data
# todo: sort so user reviews are at the top
@reviews.route("/artist/<artist_id>", methods=["GET"])
def get_artist_reviews(artist_id):
    sorted_reviews_query = (
        db.session.query(
            Review.id.label("review_id"),
            Review.spotify_id,
            Review.user_id,
            Review.comment,
            Review.rating,
            Review.created_date,
            Review.updated_date,
            Review.upvotes,
            Review.is_private,
            User.username,
            User.display_name,
        ).join(
            User, Review.user_id == User.id
        ).filter(
            Review.spotify_artist_id == artist_id,
            Review.is_private is False,
        ).order_by(
            desc(Review.upvotes),
            desc(Review.created_date),
        )
    )
    reviews = defaultdict(list)
    for review in sorted_reviews_query:
        reviews[review.spotify_id].append({
            "spotifyId": review.spotify_id,
            "reviewId": review.review_id,
            "userId": review.user_id,
            "comment": review.comment,
            "rating": review.rating,
            "createdDate": review.created_date,
            "updatedDate": review.updated_date,
            "upvotes": review.upvotes,
            "username": review.username,
            "displayName": review.display_name,
        })
    reviews_dict = dict(reviews)
    return jsonify(reviews_dict), 200


@reviews.route("/user/<user_id>", methods=["GET"])
def get_user_reviews_public(user_id):
    sorted_reviews_query = (
        db.session.query(
            Review.id.label("review_id"),
            Review.spotify_id,
            Review.user_id,
            Review.comment,
            Review.rating,
            Review.created_date,
            Review.updated_date,
            Review.upvotes,
            Review.is_private,
            User.username,
            User.display_name,
        ).join(
            User, Review.user_id == User.id
        ).filter(
            Review.user_id == user_id,
            Review.is_private is False,
        ).order_by(
            desc(Review.created_date),
        )
    )

    reviews = defaultdict(list)
    for review in sorted_reviews_query:
        reviews[review.spotify_id].append({
            "spotifyId": review.spotify_id,
            "reviewId": review.review_id,
            "userId": review.user_id,
            "comment": review.comment,
            "rating": review.rating,
            "createdDate": review.created_date,
            "updatedDate": review.updated_date,
            "upvotes": review.upvotes,
            "username": review.username,
            "displayName": review.display_name,
        })

    reviews_dict = dict(reviews)
    
    return jsonify(reviews_dict), 200
