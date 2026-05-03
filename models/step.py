from app import db
from datetime import datetime

# Association table for Step-Role many-to-many relationship (required roles)
step_required_roles = db.Table('step_required_roles',
    db.Column('step_id', db.Integer, db.ForeignKey('steps.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=db.func.now())
)

class Step(db.Model):
    """Step/Task model"""
    __tablename__ = 'steps'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    step_type = db.Column(db.String(50))  # e.g., 'model_implementation', 'sharepoint_confirmation', 'illustration', etc.
    template_id = db.Column(db.Integer, db.ForeignKey('step_templates.id'), index=True)  # Reference to template used

    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timing
    estimated_time = db.Column(db.Integer)  # in minutes/hours (store as minutes)
    actual_time = db.Column(db.Integer, default=0)  # actual time spent in minutes
    due_date = db.Column(db.DateTime, index=True)
    completed_at = db.Column(db.DateTime)

    # Status and Priority
    status = db.Column(db.String(20), default='pending', index=True)  # pending, in_progress, completed
    priority = db.Column(db.String(20), default='normal', index=True)  # normal, urgent, very_urgent

    # Project relationship (optional - steps can exist without project)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), index=True)

    # Additional fields
    notes = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)

    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Relationship to template
    template = db.relationship('StepTemplate', foreign_keys=[template_id])

    # Many-to-many relationship with required roles
    required_roles = db.relationship('Role', secondary=step_required_roles, lazy='subquery',
                                      backref=db.backref('steps', lazy=True))

    def __repr__(self):
        return f'<Step {self.name}>'

    @property
    def is_overdue(self):
        """Check if step is overdue"""
        if self.due_date and self.status != 'completed':
            return datetime.utcnow() > self.due_date
        return False

    @property
    def is_completed(self):
        """Check if step is completed"""
        return self.status == 'completed'

    def mark_completed(self):
        """Mark step as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()

    def mark_in_progress(self):
        """Mark step as in progress"""
        self.status = 'in_progress'
        self.completed_at = None

    def mark_pending(self):
        """Mark step as pending"""
        self.status = 'pending'
        self.completed_at = None

    def can_user_execute(self, user):
        """Check if user has required roles to execute this step"""
        # If no roles are required, anyone can execute
        if not self.required_roles:
            return True
        # Check if user has at least one of the required roles
        required_role_names = [role.name for role in self.required_roles]
        return user.has_any_role(required_role_names)

    def get_time_spent(self):
        """Calculate actual time spent (can be extended with time tracking)"""
        # Return actual time if set, otherwise estimated time
        return self.actual_time if self.actual_time > 0 else self.estimated_time

    def to_dict(self):
        """Convert step to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'step_type': self.step_type,
            'assigned_to': self.assigned_to,
            'assigned_to_name': self.assignee.full_name if self.assignee else None,
            'created_by': self.created_by,
            'created_by_name': self.creator.full_name if self.creator else None,
            'estimated_time': self.estimated_time,
            'actual_time': self.actual_time,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'priority': self.priority,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'is_completed': self.is_completed,
            'required_roles': [role.to_dict() for role in self.required_roles],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }