from app import db

class Notification(db.Model):
    """Notification model for in-app and email notifications"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # 'assignment', 'deadline', 'status_change', 'system'
    is_read = db.Column(db.Boolean, default=False, index=True)
    link = db.Column(db.String(500))  # Optional link to related item
    created_at = db.Column(db.DateTime, default=db.func.now(), index=True)

    def __repr__(self):
        return f'<Notification {self.title}>'

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'link': self.link,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }