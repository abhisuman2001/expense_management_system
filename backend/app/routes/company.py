from flask import Blueprint, request, jsonify
from app import db
from app.models import Company, User, ExpenseCategory
from app.utils.decorators import auth_required, admin_required
from app.utils.validators import sanitize_string

company_bp = Blueprint('company', __name__)

@company_bp.route('/info', methods=['GET'])
@auth_required
def get_company_info(current_user):
    try:
        company = current_user.company
        
        # Get company statistics
        total_employees = User.query.filter_by(company_id=company.id, is_active=True).count()
        total_managers = User.query.filter_by(company_id=company.id, role='manager', is_active=True).count()
        
        return jsonify({
            'company': {
                'id': company.id,
                'name': company.name,
                'country': company.country,
                'currency': company.currency,
                'total_employees': total_employees,
                'total_managers': total_managers,
                'created_at': company.created_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch company info', 'error': str(e)}), 500

@company_bp.route('/update', methods=['PUT'])
@admin_required
def update_company(current_user):
    try:
        data = request.get_json()
        company = current_user.company
        
        # Update allowed fields
        if 'name' in data:
            company.name = sanitize_string(data['name'], 100)
        
        if 'country' in data:
            company.country = data['country']
        
        if 'currency' in data:
            company.currency = data['currency']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Company updated successfully',
            'company': {
                'id': company.id,
                'name': company.name,
                'country': company.country,
                'currency': company.currency
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update company', 'error': str(e)}), 500

@company_bp.route('/categories', methods=['GET'])
@auth_required
def get_expense_categories(current_user):
    try:
        categories = ExpenseCategory.query.filter_by(
            company_id=current_user.company_id,
            is_active=True
        ).all()
        
        return jsonify({
            'categories': [{
                'id': cat.id,
                'name': cat.name,
                'description': cat.description
            } for cat in categories]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch categories', 'error': str(e)}), 500

@company_bp.route('/categories', methods=['POST'])
@admin_required
def create_expense_category(current_user):
    try:
        data = request.get_json()
        
        name = sanitize_string(data.get('name'), 50)
        description = sanitize_string(data.get('description', ''), 255)
        
        if not name:
            return jsonify({'message': 'Category name is required'}), 400
        
        # Check if category already exists
        existing_category = ExpenseCategory.query.filter_by(
            company_id=current_user.company_id,
            name=name
        ).first()
        
        if existing_category:
            return jsonify({'message': 'Category already exists'}), 400
        
        category = ExpenseCategory(
            name=name,
            description=description,
            company_id=current_user.company_id
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category created successfully',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create category', 'error': str(e)}), 500

@company_bp.route('/categories/<int:category_id>', methods=['PUT'])
@admin_required
def update_expense_category(current_user, category_id):
    try:
        category = ExpenseCategory.query.filter_by(
            id=category_id,
            company_id=current_user.company_id
        ).first()
        
        if not category:
            return jsonify({'message': 'Category not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            category.name = sanitize_string(data['name'], 50)
        
        if 'description' in data:
            category.description = sanitize_string(data['description'], 255)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Category updated successfully',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update category', 'error': str(e)}), 500

@company_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_expense_category(current_user, category_id):
    try:
        category = ExpenseCategory.query.filter_by(
            id=category_id,
            company_id=current_user.company_id
        ).first()
        
        if not category:
            return jsonify({'message': 'Category not found'}), 404
        
        # Soft delete
        category.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Category deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete category', 'error': str(e)}), 500