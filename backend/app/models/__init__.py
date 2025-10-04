from app import db
from datetime import datetime
from enum import Enum
import bcrypt

class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class ExpenseStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ApprovalRuleType(Enum):
    PERCENTAGE = "percentage"
    SPECIFIC_APPROVER = "specific_approver"
    HYBRID = "hybrid"

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    approval_rules = db.relationship('ApprovalRule', backref='company', lazy=True)
    expenses = db.relationship('Expense', backref='company', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for manager-employee
    manager = db.relationship('User', remote_side=[id], backref='subordinates')
    
    # Relationships
    submitted_expenses = db.relationship('Expense', foreign_keys='Expense.employee_id', backref='employee', lazy=True)
    approvals = db.relationship('Approval', backref='approver', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', backref='category', lazy=True)

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    
    amount = db.Column(db.Decimal(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    amount_in_company_currency = db.Column(db.Decimal(10, 2), nullable=False)
    exchange_rate = db.Column(db.Decimal(10, 6), nullable=False, default=1.0)
    
    description = db.Column(db.Text, nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    receipt_path = db.Column(db.String(255))
    
    status = db.Column(db.Enum(ExpenseStatus), default=ExpenseStatus.PENDING)
    
    # OCR extracted data
    merchant_name = db.Column(db.String(100))
    extracted_amount = db.Column(db.Decimal(10, 2))
    extracted_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approvals = db.relationship('Approval', backref='expense', lazy=True, cascade='all, delete-orphan')

class ApprovalRule(db.Model):
    __tablename__ = 'approval_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    rule_type = db.Column(db.Enum(ApprovalRuleType), nullable=False)
    
    # For amount-based rules
    min_amount = db.Column(db.Decimal(10, 2), default=0)
    max_amount = db.Column(db.Decimal(10, 2))
    
    # For percentage rules
    required_percentage = db.Column(db.Integer)  # e.g., 60 for 60%
    
    # For specific approver rules
    specific_approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # For manager approval requirement
    requires_manager_approval = db.Column(db.Boolean, default=True)
    
    # For sequential approvals
    approval_sequence = db.Column(db.JSON)  # Store list of approver IDs in sequence
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    specific_approver = db.relationship('User', foreign_keys=[specific_approver_id])

class Approval(db.Model):
    __tablename__ = 'approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    comments = db.Column(db.Text)
    sequence_order = db.Column(db.Integer, default=1)
    
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def approve(self, comments=None):
        self.status = ApprovalStatus.APPROVED
        self.comments = comments
        self.approved_at = datetime.utcnow()
    
    def reject(self, comments=None):
        self.status = ApprovalStatus.REJECTED
        self.comments = comments
        self.approved_at = datetime.utcnow()

# Association table for many-to-many relationship between approval rules and approvers
approval_rule_approvers = db.Table('approval_rule_approvers',
    db.Column('approval_rule_id', db.Integer, db.ForeignKey('approval_rules.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)