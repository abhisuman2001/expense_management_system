from flask import Blueprint, request, jsonify
from app import db
from app.models import User, UserRole
from app.utils.decorators import auth_required, admin_required, manager_or_admin_required
from app.utils.validators import validate_email, validate_password, sanitize_string

user_bp = Blueprint('user', __name__)

@user_bp.route('/', methods=['GET'])
@manager_or_admin_required
def get_users(current_user):
    try:
        # Query users from the same company
        query = User.query.filter_by(company_id=current_user.company_id, is_active=True)
        
        # If user is manager (not admin), only show their subordinates
        if current_user.role == UserRole.MANAGER:
            query = query.filter_by(manager_id=current_user.id)
        
        users = query.all()
        
        return jsonify({
            'users': [{
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'role': user.role.value,
                'manager_id': user.manager_id,
                'manager_name': user.manager.full_name if user.manager else None,
                'created_at': user.created_at.isoformat()
            } for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch users', 'error': str(e)}), 500

@user_bp.route('/create', methods=['POST'])
@admin_required
def create_user(current_user):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        first_name = sanitize_string(data['first_name'], 50)
        last_name = sanitize_string(data['last_name'], 50)
        role = data['role']
        manager_id = data.get('manager_id')
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'message': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'message': message}), 400
        
        # Validate role
        try:
            user_role = UserRole(role)
        except ValueError:
            return jsonify({'message': 'Invalid role'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'User with this email already exists'}), 400
        
        # Validate manager if provided
        manager = None
        if manager_id:
            manager = User.query.filter_by(
                id=manager_id,
                company_id=current_user.company_id,
                is_active=True
            ).first()
            
            if not manager:
                return jsonify({'message': 'Invalid manager'}), 400
            
            # Manager should have manager or admin role
            if manager.role not in [UserRole.MANAGER, UserRole.ADMIN]:
                return jsonify({'message': 'Manager must have manager or admin role'}), 400
        
        # Create user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=user_role,
            company_id=current_user.company_id,
            manager_id=manager_id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'manager_id': user.manager_id,
                'manager_name': user.manager.full_name if user.manager else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create user', 'error': str(e)}), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
@manager_or_admin_required
def get_user(current_user, user_id):
    try:
        # Find user in the same company
        user = User.query.filter_by(
            id=user_id,
            company_id=current_user.company_id,
            is_active=True
        ).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # If current user is manager, ensure they can only access their subordinates
        if current_user.role == UserRole.MANAGER and user.manager_id != current_user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        return jsonify({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'manager_id': user.manager_id,
                'manager_name': user.manager.full_name if user.manager else None,
                'created_at': user.created_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch user', 'error': str(e)}), 500

@user_bp.route('/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(current_user, user_id):
    try:
        # Find user in the same company
        user = User.query.filter_by(
            id=user_id,
            company_id=current_user.company_id,
            is_active=True
        ).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = sanitize_string(data['first_name'], 50)
        
        if 'last_name' in data:
            user.last_name = sanitize_string(data['last_name'], 50)
        
        if 'role' in data:
            try:
                user.role = UserRole(data['role'])
            except ValueError:
                return jsonify({'message': 'Invalid role'}), 400
        
        if 'manager_id' in data:
            manager_id = data['manager_id']
            if manager_id:
                manager = User.query.filter_by(
                    id=manager_id,
                    company_id=current_user.company_id,
                    is_active=True
                ).first()
                
                if not manager:
                    return jsonify({'message': 'Invalid manager'}), 400
                
                if manager.role not in [UserRole.MANAGER, UserRole.ADMIN]:
                    return jsonify({'message': 'Manager must have manager or admin role'}), 400
            
            user.manager_id = manager_id
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'manager_id': user.manager_id,
                'manager_name': user.manager.full_name if user.manager else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update user', 'error': str(e)}), 500

@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(current_user, user_id):
    try:
        # Find user in the same company
        user = User.query.filter_by(
            id=user_id,
            company_id=current_user.company_id
        ).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.id == current_user.id:
            return jsonify({'message': 'Cannot deactivate your own account'}), 400
        
        user.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'User deactivated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to deactivate user', 'error': str(e)}), 500

@user_bp.route('/managers', methods=['GET'])
@admin_required
def get_managers(current_user):
    try:
        managers = User.query.filter_by(
            company_id=current_user.company_id,
            is_active=True
        ).filter(User.role.in_([UserRole.MANAGER, UserRole.ADMIN])).all()
        
        return jsonify({
            'managers': [{
                'id': manager.id,
                'full_name': manager.full_name,
                'email': manager.email,
                'role': manager.role.value
            } for manager in managers]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch managers', 'error': str(e)}), 500