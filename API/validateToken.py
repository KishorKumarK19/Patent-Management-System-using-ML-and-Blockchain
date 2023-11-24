from functools import wraps
from flask import request , jsonify
import jwt
from app import app 

def validate_token_and_role(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = request.cookies.get("token")

            if not token:
                print("Token is Missing")
                return jsonify({'message': 'Token is missing'}), 401

            try:
                payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                print("Token Has Expired")
                return jsonify({'message': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                print("Invalid Token")
                return jsonify({'message': 'Invalid token'}), 401

            user_role = payload.get('role')
            if user_role != required_role:
                print("Access Denied")
                return jsonify({'message': 'Access denied'}), 403

            return fn(*args, **kwargs)

        return wrapper
    return decorator