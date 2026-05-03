from app import db

class Role(db.Model):
    """Role model - defines user roles in the system"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    # Relationships - many-to-many with users
    users = db.relationship('User', secondary='user_roles', backref=db.backref('roles', lazy='select'), lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description
        }
