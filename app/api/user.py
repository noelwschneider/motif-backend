from flask import Blueprint, jsonify
from app.models import User


user = Blueprint("user", __name__)


@user.route("/<int:user_id>", methods=['GET'])
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()

    return jsonify({
        "userId": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "profilePicUrl": user.profile_pic_url
    }), 200
