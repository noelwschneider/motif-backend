from flask import Blueprint, jsonify, request, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app import db

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

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    response = make_response(jsonify({'message': 'Login successful'}), 200)
    response.set_cookie('access_token_cookie', access_token, httponly=True, secure=True, samesite='None')
    response.set_cookie('refresh_token_cookie', refresh_token, httponly=True, secure=True, samesite='None')
    return response


@auth.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    new_refresh_token = create_refresh_token(identity=current_user)

    response = jsonify({'message': 'Token refreshed'})
    response.set_cookie('access_token_cookie', new_access_token, httponly=True, secure=True, samesite='None')
    response.set_cookie('refresh_token_cookie', new_refresh_token, httponly=True, secure=True, samesite='None')
    return response


@auth.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
    response.delete_cookie('access_token_cookie', httponly=True, secure=True, samesite='None')
    response.delete_cookie('refresh_token_cookie', httponly=True, secure=True, samesite='None')
    return response


@auth.route('/verify', methods=['GET'])
@jwt_required()
def verify():
    current_user = get_jwt_identity()
    return jsonify({'authenticated': True, 'user': current_user}), 200