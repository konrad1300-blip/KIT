from app import db
from datetime import datetime
from app.models.user import User
from app.models.skill import Skill

class StepTemplate(db.Model):
    """Step Template model - reusable patterns for steps"""
    __tablename__ = 'step_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    step_type = db.Column(db.String(50))  # e.g., 'model_implementation', 'sharepoint_confirmation', etc.
    priority = db.Column(db.String(20), default='normal')  # normal, urgent, very_urgent
    estimated_time = db.Column(db.Integer)  # in minutes
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

    # Many-to-many relationship with Skills
    required_skills = db.relationship('Skill', secondary='template_skills',
                                      lazy='subquery',
                                      backref=db.backref('step_templates', lazy=True))

    # Relationship to User (creator)
    creator = db.relationship('User', foreign_keys=[created_by], backref='step_templates')

    def __repr__(self):
        return f'<StepTemplate {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'step_type': self.step_type,
            'priority': self.priority,
            'estimated_time': self.estimated_time,
            'created_by': self.created_by,
            'created_by_name': self.creator.full_name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'required_skills': [skill.to_dict() for skill in self.required_skills]
        }

# Association table for StepTemplate-Skill many-to-many relationship
template_skills = db.Table('template_skills',
    db.Column('template_id', db.Integer, db.ForeignKey('step_templates.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=db.func.now())
)