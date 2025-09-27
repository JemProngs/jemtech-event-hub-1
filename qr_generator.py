from flask import Blueprint, send_file, request
from itsdangerous import URLSafeTimedSerializer
from io import BytesIO
import qrcode
from datetime import datetime, timedelta
from config import Config
from models import db, Event

qr_bp = Blueprint('qr', __name__)
serializer = URLSafeTimedSerializer(Config.SECRET_KEY)


def generate_event_token(event_id, expiry_hours=48):
    """Generate a signed token for event access"""
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    payload = {
        'event_id': event_id,
        'exp': expires_at.timestamp()
    }
    return serializer.dumps(payload)


def verify_event_token(token, max_age=172800):  # 48 hours
    """Verify and decode an event token"""
    try:
        payload = serializer.loads(token, max_age=max_age)
        return payload
    except:
        return None


@qr_bp.route('/generate/<int:event_id>')
def generate_qr(event_id):
    """Generate QR code for an event"""
    event = Event.query.get_or_404(event_id)
    token = generate_event_token(event_id)
    qr_url = f"{request.host_url}event/{event.public_id}?token={token}"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=Config.APP_THEME['primary'], back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Save QR code path to event
    event.qr_code = qr_url
    db.session.commit()

    return send_file(img_io, mimetype='image/png')


@qr_bp.route('/download/<int:event_id>')
def download_qr(event_id):
    """Download QR code as PNG file"""
    event = Event.query.get_or_404(event_id)

    if not event.qr_code:
        # Generate QR code if not exists
        return generate_qr(event_id)

    # Create QR code from stored URL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(event.qr_code)
    qr.make(fit=True)

    img = qr.make_image(fill_color=Config.APP_THEME['primary'], back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    filename = f"qr_code_{event.public_id}.png"
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=filename)