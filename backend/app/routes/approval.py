from flask import Blueprint, request, jsonify
from app import db
from app.models import (
    Approval, ApprovalStatus, Expense, ExpenseStatus, 
    ApprovalRule, ApprovalRuleType, User, UserRole
)
from app.utils.decorators import auth_required, manager_or_admin_required, admin_required
from app.utils.validators import sanitize_string
from datetime import datetime

approval_bp = Blueprint('approval', __name__)

@approval_bp.route('/pending', methods=['GET'])
@manager_or_admin_required
def get_pending_approvals(current_user):
    try:
        # Get approvals pending for current user
        pending_approvals = Approval.query.filter_by(
            approver_id=current_user.id,
            status=ApprovalStatus.PENDING
        ).join(Expense).filter(
            Expense.company_id == current_user.company_id
        ).order_by(Approval.created_at.desc()).all()
        
        return jsonify({
            'approvals': [{
                'id': approval.id,
                'expense_id': approval.expense_id,
                'employee_name': approval.expense.employee.full_name,
                'amount': str(approval.expense.amount_in_company_currency),
                'currency': approval.expense.expense.company.currency,
                'category': approval.expense.category.name,
                'description': approval.expense.description,
                'expense_date': approval.expense.expense_date.isoformat(),
                'receipt_path': approval.expense.receipt_path,
                'sequence_order': approval.sequence_order,
                'created_at': approval.created_at.isoformat()
            } for approval in pending_approvals]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch pending approvals', 'error': str(e)}), 500

@approval_bp.route('/<int:approval_id>/approve', methods=['POST'])
@manager_or_admin_required
def approve_expense(current_user, approval_id):
    try:
        # Find approval
        approval = Approval.query.filter_by(
            id=approval_id,
            approver_id=current_user.id,
            status=ApprovalStatus.PENDING
        ).first()
        
        if not approval:
            return jsonify({'message': 'Approval not found or already processed'}), 404
        
        # Check if expense belongs to same company
        if approval.expense.company_id != current_user.company_id:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json() or {}
        comments = sanitize_string(data.get('comments', ''), 500)
        
        # Approve the current approval
        approval.approve(comments)
        
        # Check if this completes the approval workflow
        expense = approval.expense
        _process_approval_workflow(expense)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Expense approved successfully',
            'approval': {
                'id': approval.id,
                'status': approval.status.value,
                'comments': approval.comments,
                'approved_at': approval.approved_at.isoformat()
            },
            'expense_status': expense.status.value
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to approve expense', 'error': str(e)}), 500

@approval_bp.route('/<int:approval_id>/reject', methods=['POST'])
@manager_or_admin_required
def reject_expense(current_user, approval_id):
    try:
        # Find approval
        approval = Approval.query.filter_by(
            id=approval_id,
            approver_id=current_user.id,
            status=ApprovalStatus.PENDING
        ).first()
        
        if not approval:
            return jsonify({'message': 'Approval not found or already processed'}), 404
        
        # Check if expense belongs to same company
        if approval.expense.company_id != current_user.company_id:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        comments = sanitize_string(data.get('comments', ''), 500)
        
        if not comments:
            return jsonify({'message': 'Comments are required for rejection'}), 400
        
        # Reject the approval
        approval.reject(comments)
        
        # Reject the entire expense
        expense = approval.expense
        expense.status = ExpenseStatus.REJECTED
        
        db.session.commit()
        
        return jsonify({
            'message': 'Expense rejected successfully',
            'approval': {
                'id': approval.id,
                'status': approval.status.value,
                'comments': approval.comments,
                'approved_at': approval.approved_at.isoformat()
            },
            'expense_status': expense.status.value
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to reject expense', 'error': str(e)}), 500

@approval_bp.route('/rules', methods=['GET'])
@admin_required
def get_approval_rules(current_user):
    try:
        rules = ApprovalRule.query.filter_by(
            company_id=current_user.company_id,
            is_active=True
        ).all()
        
        return jsonify({
            'rules': [{
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'rule_type': rule.rule_type.value,
                'min_amount': str(rule.min_amount) if rule.min_amount else None,
                'max_amount': str(rule.max_amount) if rule.max_amount else None,
                'required_percentage': rule.required_percentage,
                'specific_approver_id': rule.specific_approver_id,
                'specific_approver_name': rule.specific_approver.full_name if rule.specific_approver else None,
                'requires_manager_approval': rule.requires_manager_approval,
                'approval_sequence': rule.approval_sequence,
                'created_at': rule.created_at.isoformat()
            } for rule in rules]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch approval rules', 'error': str(e)}), 500

@approval_bp.route('/rules', methods=['POST'])
@admin_required
def create_approval_rule(current_user):
    try:
        data = request.get_json()
        
        name = sanitize_string(data.get('name'), 100)
        description = sanitize_string(data.get('description', ''), 500)
        rule_type = data.get('rule_type')
        
        if not name or not rule_type:
            return jsonify({'message': 'Name and rule_type are required'}), 400
        
        try:
            rule_type_enum = ApprovalRuleType(rule_type)
        except ValueError:
            return jsonify({'message': 'Invalid rule_type'}), 400
        
        # Create approval rule
        rule = ApprovalRule(
            company_id=current_user.company_id,
            name=name,
            description=description,
            rule_type=rule_type_enum,
            min_amount=data.get('min_amount'),
            max_amount=data.get('max_amount'),
            required_percentage=data.get('required_percentage'),
            specific_approver_id=data.get('specific_approver_id'),
            requires_manager_approval=data.get('requires_manager_approval', True),
            approval_sequence=data.get('approval_sequence')
        )
        
        # Validate specific approver if provided
        if rule.specific_approver_id:
            approver = User.query.filter_by(
                id=rule.specific_approver_id,
                company_id=current_user.company_id,
                is_active=True
            ).first()
            
            if not approver or approver.role not in [UserRole.MANAGER, UserRole.ADMIN]:
                return jsonify({'message': 'Invalid specific approver'}), 400
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'message': 'Approval rule created successfully',
            'rule': {
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'rule_type': rule.rule_type.value
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create approval rule', 'error': str(e)}), 500

@approval_bp.route('/history', methods=['GET'])
@manager_or_admin_required
def get_approval_history(current_user):
    try:
        # Get approvals processed by current user
        approvals = Approval.query.filter_by(
            approver_id=current_user.id
        ).filter(
            Approval.status.in_([ApprovalStatus.APPROVED, ApprovalStatus.REJECTED])
        ).join(Expense).filter(
            Expense.company_id == current_user.company_id
        ).order_by(Approval.approved_at.desc()).limit(50).all()
        
        return jsonify({
            'approvals': [{
                'id': approval.id,
                'expense_id': approval.expense_id,
                'employee_name': approval.expense.employee.full_name,
                'amount': str(approval.expense.amount_in_company_currency),
                'currency': approval.expense.expense.company.currency,
                'category': approval.expense.category.name,
                'description': approval.expense.description,
                'expense_date': approval.expense.expense_date.isoformat(),
                'status': approval.status.value,
                'comments': approval.comments,
                'approved_at': approval.approved_at.isoformat(),
                'expense_status': approval.expense.status.value
            } for approval in approvals]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch approval history', 'error': str(e)}), 500

def _process_approval_workflow(expense):
    """Process approval workflow after an approval is made"""
    try:
        # Get all approvals for this expense
        approvals = expense.approvals
        
        # Check if all required approvals are complete
        pending_approvals = [a for a in approvals if a.status == ApprovalStatus.PENDING]
        
        if not pending_approvals:
            # All approvals complete, check if expense should be approved
            rejected_approvals = [a for a in approvals if a.status == ApprovalStatus.REJECTED]
            
            if rejected_approvals:
                expense.status = ExpenseStatus.REJECTED
            else:
                expense.status = ExpenseStatus.APPROVED
        
    except Exception as e:
        # Log error but don't fail the approval
        pass