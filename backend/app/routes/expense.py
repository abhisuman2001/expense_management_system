from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Expense, ExpenseCategory, ExpenseStatus, Approval, ApprovalStatus, User, UserRole
from app.services.external_api import CurrencyService
from app.utils.decorators import auth_required, manager_or_admin_required
from app.utils.validators import sanitize_string
from datetime import datetime, date
from decimal import Decimal
import os
from werkzeug.utils import secure_filename
import uuid

expense_bp = Blueprint('expense', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@expense_bp.route('/submit', methods=['POST'])
@auth_required
def submit_expense(current_user):
    try:
        # Get form data
        amount = request.form.get('amount')
        currency = request.form.get('currency')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        expense_date = request.form.get('expense_date')
        merchant_name = request.form.get('merchant_name', '')
        
        # Validate required fields
        if not all([amount, currency, category_id, description, expense_date]):
            return jsonify({'message': 'Amount, currency, category, description, and date are required'}), 400
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                return jsonify({'message': 'Amount must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid amount format'}), 400
        
        try:
            category_id = int(category_id)
            category = ExpenseCategory.query.filter_by(
                id=category_id,
                company_id=current_user.company_id,
                is_active=True
            ).first()
            if not category:
                return jsonify({'message': 'Invalid category'}), 400
        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid category ID'}), 400
        
        try:
            expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
            if expense_date > date.today():
                return jsonify({'message': 'Expense date cannot be in the future'}), 400
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Convert amount to company currency
        company_currency = current_user.company.currency
        amount_in_company_currency, exchange_rate = CurrencyService.convert_amount(
            amount, currency, company_currency
        )
        
        if amount_in_company_currency is None:
            return jsonify({'message': 'Currency conversion failed'}), 400
        
        # Handle file upload
        receipt_path = None
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                upload_dir = os.path.join(current_app.instance_path, current_app.config['UPLOAD_FOLDER'])
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, unique_filename)
                file.save(file_path)
                receipt_path = unique_filename
        
        # Create expense
        expense = Expense(
            employee_id=current_user.id,
            company_id=current_user.company_id,
            category_id=category_id,
            amount=amount,
            currency=currency,
            amount_in_company_currency=amount_in_company_currency,
            exchange_rate=exchange_rate,
            description=sanitize_string(description, 500),
            expense_date=expense_date,
            receipt_path=receipt_path,
            merchant_name=sanitize_string(merchant_name, 100) if merchant_name else None,
            status=ExpenseStatus.PENDING
        )
        
        db.session.add(expense)
        db.session.flush()  # Get expense ID
        
        # Create approval workflow
        approval_created = _create_approval_workflow(expense, current_user)
        
        if not approval_created:
            db.session.rollback()
            return jsonify({'message': 'Failed to create approval workflow'}), 500
        
        db.session.commit()
        
        return jsonify({
            'message': 'Expense submitted successfully',
            'expense': {
                'id': expense.id,
                'amount': str(expense.amount),
                'currency': expense.currency,
                'amount_in_company_currency': str(expense.amount_in_company_currency),
                'category': expense.category.name,
                'description': expense.description,
                'expense_date': expense.expense_date.isoformat(),
                'status': expense.status.value,
                'merchant_name': expense.merchant_name
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to submit expense', 'error': str(e)}), 500

@expense_bp.route('/', methods=['GET'])
@auth_required
def get_expenses(current_user):
    try:
        # Get query parameters
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category_id = request.args.get('category_id')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Base query
        if current_user.role == UserRole.EMPLOYEE:
            # Employees can only see their own expenses
            query = Expense.query.filter_by(employee_id=current_user.id)
        else:
            # Managers and admins can see company expenses
            query = Expense.query.filter_by(company_id=current_user.company_id)
            
            # If manager, filter to their team's expenses
            if current_user.role == UserRole.MANAGER:
                subordinate_ids = [user.id for user in current_user.subordinates]
                subordinate_ids.append(current_user.id)  # Include manager's own expenses
                query = query.filter(Expense.employee_id.in_(subordinate_ids))
        
        # Apply filters
        if status:
            try:
                expense_status = ExpenseStatus(status)
                query = query.filter_by(status=expense_status)
            except ValueError:
                return jsonify({'message': 'Invalid status'}), 400
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Expense.expense_date >= start_date)
            except ValueError:
                return jsonify({'message': 'Invalid start_date format'}), 400
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Expense.expense_date <= end_date)
            except ValueError:
                return jsonify({'message': 'Invalid end_date format'}), 400
        
        if category_id:
            try:
                category_id = int(category_id)
                query = query.filter_by(category_id=category_id)
            except ValueError:
                return jsonify({'message': 'Invalid category_id'}), 400
        
        # Order by creation date (newest first)
        query = query.order_by(Expense.created_at.desc())
        
        # Paginate
        expenses = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'expenses': [{
                'id': expense.id,
                'employee_id': expense.employee_id,
                'employee_name': expense.employee.full_name,
                'amount': str(expense.amount),
                'currency': expense.currency,
                'amount_in_company_currency': str(expense.amount_in_company_currency),
                'category': expense.category.name,
                'description': expense.description,
                'expense_date': expense.expense_date.isoformat(),
                'status': expense.status.value,
                'merchant_name': expense.merchant_name,
                'receipt_path': expense.receipt_path,
                'created_at': expense.created_at.isoformat(),
                'pending_approvals': len([a for a in expense.approvals if a.status == ApprovalStatus.PENDING])
            } for expense in expenses.items],
            'pagination': {
                'page': expenses.page,
                'pages': expenses.pages,
                'per_page': expenses.per_page,
                'total': expenses.total,
                'has_next': expenses.has_next,
                'has_prev': expenses.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch expenses', 'error': str(e)}), 500

@expense_bp.route('/<int:expense_id>', methods=['GET'])
@auth_required
def get_expense(current_user, expense_id):
    try:
        # Find expense
        expense = Expense.query.filter_by(id=expense_id).first()
        
        if not expense:
            return jsonify({'message': 'Expense not found'}), 404
        
        # Check permissions
        if current_user.role == UserRole.EMPLOYEE and expense.employee_id != current_user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        if expense.company_id != current_user.company_id:
            return jsonify({'message': 'Access denied'}), 403
        
        if current_user.role == UserRole.MANAGER:
            # Manager can only see their team's expenses
            subordinate_ids = [user.id for user in current_user.subordinates]
            subordinate_ids.append(current_user.id)
            if expense.employee_id not in subordinate_ids:
                return jsonify({'message': 'Access denied'}), 403
        
        # Get approval history
        approvals = [{
            'id': approval.id,
            'approver_name': approval.approver.full_name,
            'approver_role': approval.approver.role.value,
            'status': approval.status.value,
            'comments': approval.comments,
            'sequence_order': approval.sequence_order,
            'approved_at': approval.approved_at.isoformat() if approval.approved_at else None,
            'created_at': approval.created_at.isoformat()
        } for approval in expense.approvals]
        
        return jsonify({
            'expense': {
                'id': expense.id,
                'employee_id': expense.employee_id,
                'employee_name': expense.employee.full_name,
                'amount': str(expense.amount),
                'currency': expense.currency,
                'amount_in_company_currency': str(expense.amount_in_company_currency),
                'exchange_rate': str(expense.exchange_rate),
                'category': expense.category.name,
                'description': expense.description,
                'expense_date': expense.expense_date.isoformat(),
                'status': expense.status.value,
                'merchant_name': expense.merchant_name,
                'receipt_path': expense.receipt_path,
                'created_at': expense.created_at.isoformat(),
                'updated_at': expense.updated_at.isoformat()
            },
            'approvals': approvals
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch expense', 'error': str(e)}), 500

def _create_approval_workflow(expense, employee):
    """Create approval workflow for an expense"""
    try:
        # Simple workflow: if employee has manager, create approval for manager
        if employee.manager:
            approval = Approval(
                expense_id=expense.id,
                approver_id=employee.manager_id,
                sequence_order=1,
                status=ApprovalStatus.PENDING
            )
            db.session.add(approval)
            return True
        else:
            # No manager, auto-approve (or require admin approval)
            expense.status = ExpenseStatus.APPROVED
            return True
            
    except Exception as e:
        return False

@expense_bp.route('/currencies', methods=['GET'])
@auth_required
def get_supported_currencies(current_user):
    """Get list of supported currencies for expense submission"""
    try:
        # Common currencies (you can expand this list)
        currencies = [
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
            {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'},
            {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥'},
            {'code': 'CAD', 'name': 'Canadian Dollar', 'symbol': 'C$'},
            {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': 'A$'},
            {'code': 'INR', 'name': 'Indian Rupee', 'symbol': '₹'},
            {'code': 'CNY', 'name': 'Chinese Yuan', 'symbol': '¥'},
        ]
        
        # Add company currency if not in list
        company_currency = current_user.company.currency
        if not any(c['code'] == company_currency for c in currencies):
            currencies.insert(0, {
                'code': company_currency,
                'name': company_currency,
                'symbol': company_currency
            })
        
        return jsonify({
            'currencies': currencies,
            'company_currency': company_currency
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch currencies', 'error': str(e)}), 500