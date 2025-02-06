from flask import Blueprint, jsonify, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app import db
from app.util.auth import set_user_cookies

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # todo: username, either instead of or alternative to email
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    response_data = {
        "userId": user.id,
        "username": str(user.username),
        "displayName": str(user.display_name),
        "profilePicUrl": str(user.profile_pic_url)
    }
    response = make_response(jsonify(response_data), 200)
    response = set_user_cookies(response, str(user.id))

    return response


@auth.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
    response.delete_cookie('access_token_cookie', httponly=True, secure=True, samesite='None')
    response.delete_cookie('refresh_token_cookie', httponly=True, secure=True, samesite='None')
    response.delete_cookie('csrf_access_token', samesite='None', secure=True)
    response.delete_cookie('csrf_refresh_token', samesite='None', secure=True)

    return response


@auth.route('/verify', methods=['GET'])
@jwt_required()
def verify():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    response_data = {
        "userId": str(user.id),
        "username": str(user.username),
        "displayName": str(user.display_name),
        "profilePicUrl": str(user.profile_pic_url)
    }

    return jsonify(response_data), 200
