from app import db
from app.models.project_template import ProjectTemplate

class Project(db.Model):
    """Project model"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, completed, archived
    priority = db.Column(db.Integer, default=2)  # 1: low, 2: medium, 3: high, 4: urgent
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    due_date = db.Column(db.DateTime)
    project_template_id = db.Column(db.Integer, db.ForeignKey('project_templates.id'), index=True)

    # Relationships
    steps = db.relationship('Step', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    project_template = db.relationship('ProjectTemplate', foreign_keys=[project_template_id])

    def __repr__(self):
        return f'<Project {self.name}>'

    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        total = self.steps.count()
        if total == 0:
            return 0
        completed = self.steps.filter_by(status='completed').count()
        return round((completed / total) * 100, 2)

    @property
    def priority_label(self):
        """Get priority label"""
        priority_map = {
            1: 'low',
            2: 'medium',
            3: 'high',
            4: 'urgent'
        }
        return priority_map.get(self.priority, 'medium')

    @property
    def status_priority(self):
        """Get status based on step priorities"""
        urgent_steps = self.steps.filter_by(priority='urgent', status='in_progress').count()
        very_urgent_steps = self.steps.filter_by(priority='very_urgent', status='in_progress').count()
        if very_urgent_steps > 0:
            return 'very_urgent'
        elif urgent_steps > 0:
            return 'urgent'
        return self.status

    def get_steps_by_status(self, status):
        """Get steps filtered by status"""
        return self.steps.filter_by(status=status).all()