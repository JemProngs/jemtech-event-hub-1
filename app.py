# FIXED: Proper file path handling with relative paths
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, send_from_directory
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os
from datetime import datetime, timezone, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from PIL import Image
import imagehash
import cv2
import numpy as np
from itsdangerous import URLSafeTimedSerializer

from config import Config
from models import db, init_db, User, Event, Media, CheckIn, Comment, Notification, CollageTemplate, Collage
from auth import bcrypt

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
mail = Mail(app)
csrf = CSRFProtect(app)

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Import blueprints
from auth import auth_bp
from qr_generator import qr_bp
from media_processing import media_bp
from analytics import analytics_bp
from collage_maker import collage_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(qr_bp, url_prefix='/qr')
app.register_blueprint(media_bp, url_prefix='/media')
app.register_blueprint(analytics_bp, url_prefix='/analytics')
app.register_blueprint(collage_bp, url_prefix='/collage')


# Add context processor to make datetime available in all templates
@app.context_processor
def utility_processor():
    return {
        'now': datetime.now(timezone.utc).replace(tzinfo=None),
        'utcnow': datetime.now(timezone.utc)
    }


# Utility functions
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_thumbnail(image_path, size=(300, 300)):
    """Generate thumbnail from image"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size)
            thumb_path = f"{os.path.splitext(image_path)[0]}_thumb.jpg"
            img.convert('RGB').save(thumb_path, 'JPEG', quality=85)
            return thumb_path
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None


def compute_phash(image_path):
    """Compute perceptual hash of image"""
    try:
        with Image.open(image_path) as img:
            return str(imagehash.average_hash(img))
    except Exception as e:
        print(f"Error computing pHash: {e}")
        return None


def strip_exif(image_path):
    """Remove EXIF metadata from image"""
    try:
        image = Image.open(image_path)
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        return image_without_exif
    except Exception as e:
        print(f"Error stripping EXIF: {e}")
        return Image.open(image_path)


def blur_faces(image_path, output_path=None):
    """Blur faces in image using OpenCV"""
    if output_path is None:
        output_path = image_path

    try:
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            roi = image[y:y + h, x:x + w]
            roi = cv2.GaussianBlur(roi, (99, 99), 30)
            image[y:y + h, x:x + w] = roi

        cv2.imwrite(output_path, image)
        return True
    except Exception as e:
        print(f"Error blurring faces: {e}")
        return False


def check_duplicates(event_id, phash, threshold=5):
    """Check for duplicate images based on perceptual hash"""
    uploads = Media.query.filter_by(event_id=event_id).all()
    for upload in uploads:
        if upload.perceptual_hash and imagehash.hex_to_hash(upload.perceptual_hash) - imagehash.hex_to_hash(
                phash) < threshold:
            return upload
    return None


def process_upload(file_path, event_id, consent_type):
    """Process an uploaded file"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        file_type = 'video' if file_ext in ['.mp4', '.mov', '.avi'] else 'image'

        # Get relative path from UPLOAD_FOLDER
        upload_folder = app.config['UPLOAD_FOLDER']
        relative_file_path = os.path.relpath(file_path, upload_folder)
        relative_file_path = relative_file_path.replace('\\', '/')

        if file_type == 'image':
            clean_image = strip_exif(file_path)
            clean_image.save(file_path, quality=95)

            thumb_path = generate_thumbnail(file_path)
            if thumb_path:
                relative_thumb_path = os.path.relpath(thumb_path, upload_folder)
                relative_thumb_path = relative_thumb_path.replace('\\', '/')
            else:
                relative_thumb_path = None

            phash = compute_phash(file_path)
            duplicate = check_duplicates(event_id, phash) if phash else None

            if consent_type == 'private':
                blur_faces(file_path)
        else:
            relative_thumb_path = relative_file_path
            phash = None
            duplicate = None

        upload = Media(
            event_id=event_id,
            filename=os.path.basename(file_path),
            original_filename=os.path.basename(file_path),
            file_path=relative_file_path,
            thumbnail_path=relative_thumb_path,
            file_type=file_type,
            consent_type=consent_type,
            perceptual_hash=phash,
            status='pending' if not duplicate else 'pending'
        )

        db.session.add(upload)
        db.session.commit()

        admins = User.query.filter_by(is_admin=True).all()
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                title='New Media Upload',
                message=f'New media uploaded to event #{event_id} needs moderation',
                type='info',
                action_url=f'/admin/events/{event_id}'
            )
            db.session.add(notification)

        db.session.commit()
        return True
    except Exception as e:
        print(f"Error processing upload: {e}")
        db.session.rollback()
        return False


# Auth functions
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated_function


# User loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Serve uploaded files - FIXED: Proper relative path handling
@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        if '..' in filename or filename.startswith('/'):
            return "Invalid filename", 400

        filename = filename.replace('\\', '/').lstrip('/')
        uploads_folder = app.config['UPLOAD_FOLDER']

        # Ensure we're serving from the correct uploads directory
        return send_from_directory(uploads_folder, filename)
    except FileNotFoundError:
        return "File not found", 404


# Serve banner images specifically
@app.route('/static/uploads/banners/<filename>')
def serve_banner(filename):
    try:
        banners_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'banners')
        return send_from_directory(banners_folder, filename)
    except FileNotFoundError:
        return "Banner not found", 404


# Serve media files specifically
@app.route('/static/uploads/media/<path:filename>')
def serve_media(filename):
    try:
        media_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'media')
        return send_from_directory(media_folder, filename)
    except FileNotFoundError:
        return "Media file not found", 404


# Helper function to make datetime comparisons safe
def make_naive(dt):
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


# Routes
@app.route('/')
def index():
    now = make_naive(datetime.now(timezone.utc))
    featured_events = Event.query.filter(Event.status == 'approved', Event.start_date >= now).order_by(
        Event.created_at.desc()).limit(6).all()
    recent_media = Media.query.filter(Media.status == 'approved').order_by(Media.created_at.desc()).limit(12).all()

    return render_template('index.html', featured_events=featured_events, recent_media=recent_media, now=now)


@app.route('/events')
def events_list():
    category = request.args.get('category')
    location = request.args.get('location')
    date_filter = request.args.get('date')
    now = make_naive(datetime.now(timezone.utc))

    query = Event.query.filter(Event.status == 'approved')

    if category and category != 'all':
        query = query.filter(Event.category == category)
    if location:
        query = query.filter(Event.location.ilike(f'%{location}%'))
    if date_filter:
        if date_filter == 'today':
            query = query.filter(Event.start_date >= now.date())
        elif date_filter == 'week':
            query = query.filter(Event.start_date >= now.date(), Event.start_date <= now.date() + timedelta(days=7))
        elif date_filter == 'month':
            query = query.filter(Event.start_date >= now.date(), Event.start_date <= now.date() + timedelta(days=30))

    events = query.order_by(Event.start_date.asc()).all()
    categories = [cat[0] for cat in db.session.query(Event.category).distinct().all()]

    return render_template('event/events_list.html', events=events, categories=categories, selected_category=category,
                           selected_location=location, selected_date=date_filter)


@app.route('/event/<public_id>')
def event_public_page(public_id):
    event = Event.query.filter_by(public_id=public_id).first_or_404()

    if event.status != 'approved':
        flash('This event is not available.', 'warning')
        return redirect(url_for('index'))

    media = Media.query.filter_by(event_id=event.id, status='approved').order_by(Media.created_at.desc()).all()
    comments = Comment.query.filter_by(event_id=event.id, status='approved').order_by(Comment.created_at.desc()).all()
    checkins = CheckIn.query.filter_by(event_id=event.id).all()

    return render_template('event/public_page.html', event=event, media=media, comments=comments, checkins=checkins)


@app.route('/event/<public_id>/gallery')
def event_gallery(public_id):
    event = Event.query.filter_by(public_id=public_id).first_or_404()

    if event.status != 'approved':
        flash('This event is not available.', 'warning')
        return redirect(url_for('index'))

    media = Media.query.filter_by(event_id=event.id, status='approved').order_by(Media.created_at.desc()).all()
    return render_template('event/gallery.html', event=event, media=media)


@app.route('/event/<public_id>/upload', methods=['GET', 'POST'])
def event_upload(public_id):
    event = Event.query.filter_by(public_id=public_id).first_or_404()

    if event.status != 'approved':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'This event is not available.'}), 400
        flash('This event is not available.', 'warning')
        return redirect(url_for('index'))

    now = make_naive(datetime.now(timezone.utc))
    event_end_date = make_naive(event.end_date) if hasattr(event.end_date,
                                                           'tzinfo') and event.end_date.tzinfo else event.end_date

    if event_end_date < now:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'This event has ended. Uploads are no longer accepted.'}), 400
        flash('This event has ended. Uploads are no longer accepted.', 'warning')
        return redirect(url_for('event_public_page', public_id=public_id))

    if request.method == 'POST':
        if 'files' not in request.files:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': 'No files selected.'}), 400
            flash('No files selected.', 'danger')
            return redirect(request.url)

        files = request.files.getlist('files')
        consent_type = request.form.get('consent', 'public')
        author_name = request.form.get('author_name', 'Anonymous')

        if not files or not files[0].filename:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': 'No files selected.'}), 400
            flash('No files selected.', 'danger')
            return redirect(request.url)

        successful_uploads = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                event_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'media', str(event.id))
                os.makedirs(event_folder, exist_ok=True)
                file_path = os.path.join(event_folder, f"{now.timestamp()}_{filename}")
                file.save(file_path)

                if process_upload(file_path, event.id, consent_type):
                    successful_uploads += 1

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded {successful_uploads} file(s). They will be visible after approval.',
                'uploaded_count': successful_uploads
            })

        flash(f'Successfully uploaded {successful_uploads} file(s). They will be visible after approval.', 'success')
        return redirect(url_for('event_public_page', public_id=public_id))

    return render_template('event/upload.html', event=event)


@app.route('/scan')
@login_required
def scan_qr():
    return render_template('scanner.html')


@app.route('/api/checkin', methods=['POST'])
@limiter.limit("10 per minute")
def api_checkin():
    try:
        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({'error': 'No token provided'}), 400

        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            event_data = serializer.loads(token, max_age=172800)
        except:
            return jsonify({'error': 'Invalid or expired token'}), 400

        event = db.session.get(Event, event_data['event_id'])
        if not event or event.status != 'approved':
            return jsonify({'error': 'Event not found or not approved'}), 404

        checkin = CheckIn(
            event_id=event.id,
            checked_in_at=make_naive(datetime.now(timezone.utc)),
            session_id=request.remote_addr
        )
        db.session.add(checkin)
        db.session.commit()

        return jsonify({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'public_id': event.public_id
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/comment', methods=['POST'])
def api_comment():
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            return jsonify({'error': 'CSRF token missing'}), 403

        event_id = request.form.get('event_id')
        media_id = request.form.get('media_id')
        author_name = request.form.get('author_name', 'Anonymous')
        content = request.form.get('content')

        if not event_id or not content:
            return jsonify({'error': 'Missing required fields'}), 400

        event = db.session.get(Event, event_id)
        if not event or event.status != 'approved':
            return jsonify({'error': 'Event not found or not approved'}), 404

        comment = Comment(
            event_id=event_id,
            media_id=media_id,
            author_name=author_name[:100],
            content=content
        )

        db.session.add(comment)
        db.session.commit()

        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'author_name': comment.author_name,
                'content': comment.content,
                'created_at': comment.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/like/<int:media_id>', methods=['POST'])
def api_like(media_id):
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            return jsonify({'error': 'CSRF token missing'}), 403

        media = db.session.get(Media, media_id)

        if not media or media.status != 'approved':
            return jsonify({'error': 'Media not available'}), 404

        media.likes += 1
        db.session.commit()

        return jsonify({
            'success': True,
            'likes': media.likes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# FIXED: Add missing api_report endpoint
@app.route('/api/report/<int:event_id>')
@login_required
@admin_required
def api_report(event_id):
    """Generate event report"""
    try:
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        # Generate report data
        media_count = Media.query.filter_by(event_id=event_id).count()
        approved_media = Media.query.filter_by(event_id=event_id, status='approved').count()
        pending_media = Media.query.filter_by(event_id=event_id, status='pending').count()
        checkin_count = CheckIn.query.filter_by(event_id=event_id).count()

        return jsonify({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'public_id': event.public_id
            },
            'stats': {
                'media_count': media_count,
                'approved_media': approved_media,
                'pending_media': pending_media,
                'checkin_count': checkin_count
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Admin routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_events = Event.query.count()
    total_users = User.query.count()
    total_media = Media.query.count()
    pending_events = Event.query.filter_by(status='pending').count()
    pending_media = Media.query.filter_by(status='pending').count()
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_events=total_events,
                           total_users=total_users,
                           total_media=total_media,
                           pending_events=pending_events,
                           pending_media=pending_media,
                           recent_events=recent_events)


@app.route('/admin/events')
@login_required
@admin_required
def admin_events():
    status_filter = request.args.get('status', 'all')
    query = Event.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    events = query.order_by(Event.created_at.desc()).all()

    return render_template('admin/events.html', events=events, status_filter=status_filter)


@app.route('/admin/events/<int:event_id>')
@login_required
@admin_required
def admin_event_detail(event_id):
    event = db.session.get(Event, event_id)
    media = Media.query.filter_by(event_id=event_id).order_by(Media.created_at.desc()).all()
    checkins = CheckIn.query.filter_by(event_id=event_id).order_by(CheckIn.checked_in_at.desc()).all()

    return render_template('admin/event_detail.html', event=event, media=media, checkins=checkins)


@app.route('/admin/events/<int:event_id>/<action>')
@login_required
@admin_required
def admin_event_action(event_id, action):
    event = db.session.get(Event, event_id)

    if action == 'approve':
        event.status = 'approved'
        flash('Event approved successfully.', 'success')
    elif action == 'reject':
        event.status = 'rejected'
        flash('Event rejected.', 'success')
    elif action == 'delete':
        db.session.delete(event)
        flash('Event deleted successfully.', 'success')
    else:
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin_events'))

    db.session.commit()
    return redirect(url_for('admin_events'))


@app.route('/admin/media/<int:media_id>/<action>')
@login_required
@admin_required
def admin_media_action(media_id, action):
    media = db.session.get(Media, media_id)

    if action == 'approve':
        media.status = 'approved'
        flash('Media approved successfully.', 'success')
    elif action == 'reject':
        media.status = 'rejected'
        flash('Media rejected.', 'success')
    elif action == 'delete':
        full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], media.file_path)
        if os.path.exists(full_file_path):
            os.remove(full_file_path)
        if media.thumbnail_path:
            full_thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], media.thumbnail_path)
            if os.path.exists(full_thumb_path):
                os.remove(full_thumb_path)

        db.session.delete(media)
        flash('Media deleted successfully.', 'success')
    else:
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin_event_detail', event_id=media.event_id))

    db.session.commit()
    return redirect(url_for('admin_event_detail', event_id=media.event_id))


# User Management Routes
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/<int:user_id>/<action>')
@login_required
@admin_required
def admin_user_action(user_id, action):
    user = db.session.get(User, user_id)

    if action == 'activate':
        user.is_active = True
        flash('User activated successfully.', 'success')
    elif action == 'deactivate':
        user.is_active = False
        flash('User deactivated successfully.', 'success')
    elif action == 'make_admin':
        user.is_admin = True
        flash('User granted admin privileges.', 'success')
    elif action == 'remove_admin':
        user.is_admin = False
        flash('User admin privileges removed.', 'success')
    elif action == 'delete':
        db.session.delete(user)
        flash('User deleted successfully.', 'success')
    else:
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin_users'))

    db.session.commit()
    return redirect(url_for('admin_users'))


# Analytics Routes
@app.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    total_events = Event.query.count()
    total_users = User.query.count()
    total_media = Media.query.count()
    total_checkins = CheckIn.query.count()
    top_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()

    from sqlalchemy import func
    top_locations = db.session.query(
        Event.location,
        func.count(Event.id).label('count')
    ).group_by(Event.location).order_by(func.count(Event.id).desc()).limit(5).all()

    analytics_data = {
        'total_events': total_events,
        'total_users': total_users,
        'total_media': total_media,
        'total_checkins': total_checkins,
        'approved_media': Media.query.filter_by(status='approved').count(),
        'pending_media': Media.query.filter_by(status='pending').count(),
        'rejected_media': Media.query.filter_by(status='rejected').count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'admin_users': User.query.filter_by(is_admin=True).count()
    }

    return render_template('admin/analytics.html',
                           analytics_data=analytics_data,
                           top_events=top_events,
                           top_locations=top_locations,
                           now=make_naive(datetime.now(timezone.utc)))


# User routes
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    user_events = Event.query.filter_by(created_by=current_user.id).order_by(Event.created_at.desc()).all()
    pending_events = [e for e in user_events if e.status == 'pending']
    approved_events = [e for e in user_events if e.status == 'approved']
    rejected_events = [e for e in user_events if e.status == 'rejected']

    return render_template('user/dashboard.html',
                           pending_events=pending_events,
                           approved_events=approved_events,
                           rejected_events=rejected_events)


@app.route('/user/events/create', methods=['GET', 'POST'])
@login_required
def user_create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        short_description = request.form.get('short_description')
        location = request.form.get('location')
        category = request.form.get('category')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')

        banner_image = None
        if 'banner_image' in request.files:
            file = request.files['banner_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                banners_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'banners')
                os.makedirs(banners_dir, exist_ok=True)
                banner_path = os.path.join(banners_dir,
                                           f"{make_naive(datetime.now(timezone.utc)).timestamp()}_{filename}")
                file.save(banner_path)
                # Store only the filename, not the full path
                banner_image = os.path.basename(banner_path)

        event = Event(
            title=title,
            description=description,
            short_description=short_description,
            location=location,
            category=category,
            start_date=start_date,
            end_date=end_date,
            banner_image=banner_image,  # Store only filename
            created_by=current_user.id
        )

        db.session.add(event)
        db.session.commit()

        flash('Event created successfully! It will be reviewed by an administrator.', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('user/create_event.html')


@app.route('/user/events')
@login_required
def user_events():
    status_filter = request.args.get('status', 'all')
    query = Event.query.filter_by(created_by=current_user.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    events = query.order_by(Event.created_at.desc()).all()

    return render_template('user/my_events.html', events=events, status_filter=status_filter)


@app.route('/user/events/<int:event_id>')
@login_required
def user_event_detail(event_id):
    event = db.session.get(Event, event_id)

    if event.created_by != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this event.', 'danger')
        return redirect(url_for('user_dashboard'))

    media = Media.query.filter_by(event_id=event_id).order_by(Media.created_at.desc()).all()
    checkins = CheckIn.query.filter_by(event_id=event_id).order_by(CheckIn.checked_in_at.desc()).all()

    return render_template('user/event_detail.html', event=event, media=media, checkins=checkins)


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(413)
def too_large(error):
    return render_template('errors/413.html'), 413


# Database fix route
@app.route('/fix-database-paths')
def fix_database_paths():
    """Fix existing database paths"""
    try:
        # Fix media paths
        media_items = Media.query.all()
        for media in media_items:
            if media.file_path and 'jemtech-event-hub' in media.file_path:
                new_path = media.file_path.split('jemtech-event-hub\\uploads\\')[-1].replace('\\', '/')
                media.file_path = new_path

            if media.thumbnail_path and 'jemtech-event-hub' in media.thumbnail_path:
                new_path = media.thumbnail_path.split('jemtech-event-hub\\uploads\\')[-1].replace('\\', '/')
                media.thumbnail_path = new_path

        # Fix event banners - store only filename
        events = Event.query.all()
        for event in events:
            if event.banner_image:
                if 'jemtech-event-hub' in event.banner_image:
                    # Extract just the filename
                    new_path = os.path.basename(event.banner_image)
                    event.banner_image = new_path
                elif '/' in event.banner_image or '\\' in event.banner_image:
                    # If it contains path separators, extract just the filename
                    new_path = os.path.basename(event.banner_image)
                    event.banner_image = new_path

        db.session.commit()
        return "Database paths fixed successfully!"
    except Exception as e:
        return f"Error fixing paths: {str(e)}"


if __name__ == '__main__':
    with app.app_context():
        init_db()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'media'), exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'banners'), exist_ok=True)
        os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

    app.run(debug=True)