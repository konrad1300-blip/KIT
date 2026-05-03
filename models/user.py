from app import db
from flask_login import UserMixin

# Association table for User-Role many-to-many relationship
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=db.func.now())
)

class User(db.Model, UserMixin):
    """User model with authentication and roles"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Relationships
    skills = db.relationship('Skill', secondary='user_skills', backref='users', lazy='dynamic')
    assigned_steps = db.relationship('Step', foreign_keys='Step.assigned_to', backref='assignee', lazy='dynamic')
    created_steps = db.relationship('Step', foreign_keys='Step.created_by', backref='creator', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    logs = db.relationship('Log', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='author')

    def __repr__(self):
        return f'<User {self.username}>'

    def get_id(self):
        return str(self.id)

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return self.username

    def has_skill(self, skill_name):
        """Check if user has a specific skill"""
        return self.skills.filter_by(name=skill_name).first() is not None

    def get_skills_list(self):
        """Get list of skill names"""
        return [skill.name for skill in self.skills]

    def has_role(self, role_name):
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)

    def has_any_role(self, role_names):
        """Check if user has any of the specified roles"""
        if not role_names:
            return True
        return any(role.name in role_names for role in self.roles)

    def get_roles_list(self):
        """Get list of role names"""
        return [role.name for role in self.roles]