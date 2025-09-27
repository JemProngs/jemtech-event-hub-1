from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    events = db.relationship('Event', backref='creator', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300))
    location = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    banner_image = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    qr_code = db.Column(db.String(500))
    public_id = db.Column(db.String(50), unique=True, default=lambda: str(uuid.uuid4()))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    media = db.relationship('Media', backref='event', lazy=True)
    checkins = db.relationship('CheckIn', backref='event', lazy=True)
    comments = db.relationship('Comment', backref='event', lazy=True)


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    file_type = db.Column(db.String(20))  # image, video
    consent_type = db.Column(db.String(20), default='public')  # public, private
    perceptual_hash = db.Column(db.String(64))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    comments = db.relationship('Comment', backref='media', lazy=True)


class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    checked_in_at = db.Column(db.DateTime, nullable=False)
    checked_out_at = db.Column(db.DateTime)
    session_id = db.Column(db.String(100))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    author_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='approved')  # approved, flagged


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20))  # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    action_url = db.Column(db.String(500))


class CollageTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    layout_config = db.Column(db.Text)  # JSON string with layout configuration
    category = db.Column(db.String(50))  # wedding, birthday, corporate, etc.
    thumbnail_path = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Collage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('collage_template.id'))
    title = db.Column(db.String(200))
    config_data = db.Column(db.Text)  # JSON string with collage configuration
    output_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    template = db.relationship('CollageTemplate', backref='collages')


def init_db():
    db.create_all()
    # Create admin user if not exists
    from auth import bcrypt
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@jemtech.com',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            first_name='System',
            last_name='Administrator',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()