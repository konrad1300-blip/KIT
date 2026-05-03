from app import db

class Log(db.Model):
    """Audit log for tracking all important actions"""
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'create_project', 'update_step', 'login'
    resource_type = db.Column(db.String(50))  # e.g., 'project', 'step', 'user'
    resource_id = db.Column(db.Integer)  # ID of affected resource
    details = db.Column(db.Text)  # JSON or text description of changes
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.now(), index=True)

    def __repr__(self):
        return f'<Log {self.action}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }