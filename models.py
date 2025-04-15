from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class StreamSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(100), nullable=False)
    stream_url = db.Column(db.String(255), nullable=True)  # Add this field

    teacher = db.relationship('User', backref='stream_sessions')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('stream_session.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    join_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    session = db.relationship('StreamSession', backref='attendances')
    student = db.relationship('User', backref='attendances')

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('stream_session.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    session = db.relationship('StreamSession', backref='resources')

class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('stream_session.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'raise_hand', 'question', 'message'
    content = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    session = db.relationship('StreamSession', backref='interactions')
    student = db.relationship('User', backref='interactions')