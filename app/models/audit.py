from datetime import datetime
from app.extensions import db

class AuditLog(db.Model):
    """Audit log for security and compliance"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    details = db.Column(db.Text)
    status = db.Column(db.String(20), default='success')  # success, failure
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'
