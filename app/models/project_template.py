from app import db
from datetime import datetime
from app.models.user import User
from app.models.step_template import StepTemplate

class ProjectTemplate(db.Model):
    """Project Template model - reusable patterns for projects consisting of step templates"""
    __tablename__ = 'project_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

    # Many-to-many relationship with StepTemplate (steps in the project)
    step_templates = db.relationship('StepTemplate', secondary='project_template_steps',
                                     lazy='subquery',
                                     backref=db.backref('project_templates', lazy=True))

    # Relationship to User (creator)
    creator = db.relationship('User', foreign_keys=[created_by], backref='project_templates')

    def __repr__(self):
        return f'<ProjectTemplate {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_by_name': self.creator.full_name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'step_templates': [st.to_dict() for st in self.step_templates]
        }

# Association table for ProjectTemplate-StepTemplate many-to-many relationship
project_template_steps = db.Table('project_template_steps',
    db.Column('project_template_id', db.Integer, db.ForeignKey('project_templates.id'), primary_key=True),
    db.Column('step_template_id', db.Integer, db.ForeignKey('step_templates.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=db.func.now())
)