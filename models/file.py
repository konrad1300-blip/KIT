from app import db

class File(db.Model):
    """File model with versioning support"""
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    mime_type = db.Column(db.String(100))

    # Relationships
    step_id = db.Column(db.Integer, db.ForeignKey('steps.id'), index=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Versioning
    version = db.Column(db.Integer, default=1)
    parent_file_id = db.Column(db.Integer, db.ForeignKey('files.id'))  # For version chain
    is_current = db.Column(db.Boolean, default=True)

    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=db.func.now())

    # Relationships
    step = db.relationship('Step', backref='files')
    uploader = db.relationship('User', backref='uploaded_files')
    parent_file = db.relationship('File', remote_side=[id], backref='versions')

    def __repr__(self):
        return f'<File {self.original_filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'step_id': self.step_id,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.full_name if self.uploader else None,
            'version': self.version,
            'is_current': self.is_current,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }