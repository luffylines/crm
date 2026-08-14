"""
Database models for Admin Dashboard, User Management, and Audit Logging.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and role-based access control."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')  # Admin, User, Viewer
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationship to activity logs
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, foreign_keys='ActivityLog.user_id')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class ActivityLog(db.Model):
    """Activity log model for audit trail."""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)  # LOGIN, LOGOUT, EDIT_LEAD, SAVE_LEAD, etc.
    description = db.Column(db.String(255), nullable=True)
    lead_id = db.Column(db.String(255), nullable=True)  # File key or lead identifier
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv4 and IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    changes = db.Column(db.Text, nullable=True)  # JSON-encoded changes for audits (e.g., field before/after)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert activity log to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'action': self.action,
            'description': self.description,
            'lead_id': self.lead_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'changes': self.changes,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ActivityLog {self.user.username} - {self.action}>'
