from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models import User, UserRole

def auth_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            if not current_user or not current_user.is_active:
                return jsonify({'message': 'Invalid or inactive user'}), 401
            return f(current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Authentication failed'}), 401
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return jsonify({'message': 'Insufficient permissions'}), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required(UserRole.ADMIN)(f)

def manager_or_admin_required(f):
    return role_required(UserRole.ADMIN, UserRole.MANAGER)(f)

def same_company_required(f):
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        # This decorator ensures users can only access data from their own company
        return f(current_user, *args, **kwargs)
    return decorated_function