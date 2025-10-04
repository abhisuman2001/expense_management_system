from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, Company, UserRole, ExpenseCategory
from app.utils.validators import validate_email, validate_password, sanitize_string
from app.utils.decorators import auth_required
import requests

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'company_name', 'country']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        first_name = sanitize_string(data['first_name'], 50)
        last_name = sanitize_string(data['last_name'], 50)
        company_name = sanitize_string(data['company_name'], 100)
        country = data['country']
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'message': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'message': message}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'User already exists'}), 400
        
        # Get currency for the country
        try:
            response = requests.get('https://restcountries.com/v3.1/all?fields=name,currencies')
            countries_data = response.json()
            
            currency = None
            for country_data in countries_data:
                if country_data['name']['common'].lower() == country.lower():
                    currencies = country_data.get('currencies', {})
                    if currencies:
                        currency = list(currencies.keys())[0]
                    break
            
            if not currency:
                return jsonify({'message': 'Invalid country or currency not found'}), 400
                
        except Exception as e:
            return jsonify({'message': 'Failed to fetch country data'}), 500
        
        # Create company
        company = Company(
            name=company_name,
            country=country,
            currency=currency
        )
        db.session.add(company)
        db.session.flush()  # Get company ID
        
        # Create admin user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            company_id=company.id
        )
        user.set_password(password)
        
        db.session.add(user)
        
        # Create default expense categories
        default_categories = [
            {'name': 'Travel', 'description': 'Travel expenses including flights, hotels, taxis'},
            {'name': 'Meals', 'description': 'Business meals and entertainment'},
            {'name': 'Office Supplies', 'description': 'Office equipment and supplies'},
            {'name': 'Training', 'description': 'Training and education expenses'},
            {'name': 'Internet/Phone', 'description': 'Communication expenses'},
            {'name': 'Other', 'description': 'Other business expenses'}
        ]
        
        for cat_data in default_categories:
            category = ExpenseCategory(
                name=cat_data['name'],
                description=cat_data['description'],
                company_id=company.id
            )
            db.session.add(category)
        
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Registration successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'company_id': user.company_id,
                'company_name': company.name,
                'company_currency': company.currency
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'message': 'Account is deactivated'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'company_id': user.company_id,
                'company_name': user.company.name,
                'company_currency': user.company.currency,
                'manager_id': user.manager_id
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile(current_user):
    try:
        return jsonify({
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'role': current_user.role.value,
                'company_id': current_user.company_id,
                'company_name': current_user.company.name,
                'company_currency': current_user.company.currency,
                'manager_id': current_user.manager_id,
                'manager_name': current_user.manager.full_name if current_user.manager else None
            }
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch profile', 'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@auth_required
def change_password(current_user):
    try:
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'message': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'message': 'Current password is incorrect'}), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'message': message}), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to change password', 'error': str(e)}), 500