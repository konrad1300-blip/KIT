from app import db

class Comment(db.Model):
    """Comment model for task discussions"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    step_id = db.Column(db.Integer, db.ForeignKey('steps.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Relationships
    step = db.relationship('Step', backref=db.backref('comments', lazy='dynamic'))
    author = db.relationship('User', back_populates='comments')

    def __repr__(self):
        return f'<Comment {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'step_id': self.step_id,
            'user_id': self.user_id,
            'author_name': self.author.full_name if self.author else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }