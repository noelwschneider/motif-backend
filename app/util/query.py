from app import db
from app.models import Catalog, Review, User
from collections import defaultdict
from sqlalchemy.sql import desc


def get_public_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    reviews = get_public_user_reviews(user_id)
    catalogs = []

    return {
        "userId": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "profilePicUrl": user.profile_pic_url,
        "catalogs": catalogs,
        "reviews": reviews,
    }


def get_public_user_catalogs(user_id):
    print('todo')


def get_public_user_reviews(user_id):
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
    return reviews_dict


def get_current_user_reviews(user_id):
    reviews = Review.query.filter_by(user_id=user_id).all()

    return [
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
    ]
