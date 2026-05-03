from app import db

class Skill(db.Model):
    """Skill model - predefined skills for users"""
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # e.g., 'technical', 'design', 'management'
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Skill {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category
        }

# Association table for User-Skill many-to-many relationship
user_skills = db.Table('user_skills',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=db.func.now())
)