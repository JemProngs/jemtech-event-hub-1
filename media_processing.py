from flask import Blueprint, request, jsonify, current_app
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import os
from datetime import datetime
import imagehash
import cv2
import numpy as np
from models import db, Media, Notification, User
from werkzeug.utils import secure_filename

media_bp = Blueprint('media', __name__)

# Image filters
FILTERS = {
    'normal': lambda img: img,
    'grayscale': lambda img: img.convert('L'),
    'sepia': lambda img: apply_sepia(img),
    'vintage': lambda img: apply_vintage(img),
    'warm': lambda img: apply_warm(img),
    'cool': lambda img: apply_cool(img),
    'clarity': lambda img: apply_clarity(img),
    'brightness': lambda img: ImageEnhance.Brightness(img).enhance(1.2),
    'contrast': lambda img: ImageEnhance.Contrast(img).enhance(1.2),
    'blur': lambda img: img.filter(ImageFilter.BLUR),
    'sharpen': lambda img: img.filter(ImageFilter.SHARPEN),
    'edges': lambda img: img.filter(ImageFilter.FIND_EDGES),
}


def apply_sepia(img):
    width, height = img.size
    pixels = img.load()

    for py in range(height):
        for px in range(width):
            r, g, b = img.getpixel((px, py))

            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)

            if tr > 255: tr = 255
            if tg > 255: tg = 255
            if tb > 255: tb = 255

            pixels[px, py] = (tr, tg, tb)

    return img


def apply_vintage(img):
    # Apply sepia first
    img = apply_sepia(img)
    # Then reduce contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(0.8)
    # Add vignette effect
    img = add_vignette(img, 0.8)
    return img


def apply_warm(img):
    # Split into RGB channels
    r, g, b = img.split()

    # Enhance red and green channels
    r = ImageEnhance.Brightness(r).enhance(1.2)
    g = ImageEnhance.Brightness(g).enhance(1.1)

    # Merge back
    return Image.merge('RGB', (r, g, b))


def apply_cool(img):
    # Split into RGB channels
    r, g, b = img.split()

    # Enhance blue channel
    b = ImageEnhance.Brightness(b).enhance(1.2)

    # Merge back
    return Image.merge('RGB', (r, g, b))


def apply_clarity(img):
    # Enhance contrast and sharpness
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    return img


def add_vignette(img, alpha=0.8):
    width, height = img.size
    x_center, y_center = width // 2, height // 2
    max_dist = ((x_center ** 2 + y_center ** 2) ** 0.5) * 0.8

    pixels = img.load()
    for y in range(height):
        for x in range(width):
            dist = ((x - x_center) ** 2 + (y - y_center) ** 2) ** 0.5
            factor = 1 - min(dist / max_dist, 1) * alpha

            r, g, b = pixels[x, y]
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)

            pixels[x, y] = (r, g, b)

    return img


def blur_faces(image_path, output_path=None):
    """Blur faces in image using OpenCV"""
    if output_path is None:
        output_path = image_path

    try:
        # Load the image
        image = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Load face detector
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # Blur each face
        for (x, y, w, h) in faces:
            roi = image[y:y + h, x:x + w]
            roi = cv2.GaussianBlur(roi, (99, 99), 30)
            image[y:y + h, x:x + w] = roi

        # Save the result
        cv2.imwrite(output_path, image)
        return True

    except Exception as e:
        current_app.logger.error(f"Error blurring faces: {e}")
        return False


def strip_exif(image_path):
    """Remove EXIF metadata from image"""
    try:
        image = Image.open(image_path)
        # Create new image without EXIF data
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        return image_without_exif
    except Exception as e:
        current_app.logger.error(f"Error stripping EXIF: {e}")
        return Image.open(image_path)


def generate_thumbnail(image_path, size=(300, 300)):
    """Generate thumbnail from image"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            thumb_path = f"{os.path.splitext(image_path)[0]}_thumb.jpg"
            img.convert('RGB').save(thumb_path, 'JPEG', quality=85)
            return thumb_path
    except Exception as e:
        current_app.logger.error(f"Error generating thumbnail: {e}")
        return None


def compute_phash(image_path):
    """Compute perceptual hash of image"""
    try:
        with Image.open(image_path) as img:
            return str(imagehash.average_hash(img))
    except Exception as e:
        current_app.logger.error(f"Error computing pHash: {e}")
        return None


def check_duplicates(event_id, phash, threshold=5):
    """Check for duplicate images based on perceptual hash"""
    uploads = Media.query.filter_by(event_id=event_id).all()
    for upload in uploads:
        if upload.perceptual_hash and imagehash.hex_to_hash(upload.perceptual_hash) - imagehash.hex_to_hash(
                phash) < threshold:
            return upload
    return None


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def process_upload(file_path, event_id, consent_type, author_name=None):
    """Process an uploaded file"""
    try:
        # Determine file type
        file_ext = os.path.splitext(file_path)[1].lower()
        file_type = 'video' if file_ext in ['.mp4', '.mov', '.avi'] else 'image'

        # For images, process them
        if file_type == 'image':
            # Strip EXIF data
            clean_image = strip_exif(file_path)
            clean_image.save(file_path, quality=95)

            # Generate thumbnail
            thumb_path = generate_thumbnail(file_path)

            # Compute perceptual hash
            phash = compute_phash(file_path)

            # Check for duplicates
            duplicate = check_duplicates(event_id, phash) if phash else None

            # Apply face blurring for privacy if needed
            if consent_type == 'private':
                blur_faces(file_path)

        # For videos, just generate a thumbnail from first frame
        else:
            # Video processing would go here
            thumb_path = generate_video_thumbnail(file_path)
            phash = None
            duplicate = None

        # Save to database
        upload = Media(
            event_id=event_id,
            filename=os.path.basename(file_path),
            original_filename=os.path.basename(file_path),
            file_path=file_path,
            thumbnail_path=thumb_path,
            file_type=file_type,
            consent_type=consent_type,
            perceptual_hash=phash,
            status='pending' if not duplicate else 'pending'  # Still needs moderation
        )

        db.session.add(upload)
        db.session.commit()

        # Create notification for admin
        admins = User.query.filter_by(is_admin=True).all()
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                title='New Media Upload',
                message=f'New media uploaded to event #{event_id} needs moderation',
                type='info',
                action_url=f'/admin/media?event={event_id}'
            )
            db.session.add(notification)

        db.session.commit()

        return True
    except Exception as e:
        current_app.logger.error(f"Error processing upload: {e}")
        return False


@media_bp.route('/apply-filter', methods=['POST'])
def apply_filter_endpoint():
    """Apply filter to an image"""
    try:
        media_id = request.form.get('media_id')
        filter_name = request.form.get('filter')

        media = Media.query.get_or_404(media_id)

        if media.file_type != 'image':
            return jsonify({'error': 'Only images can be filtered'}), 400

        if filter_name not in FILTERS:
            return jsonify({'error': 'Invalid filter'}), 400

        # Apply filter
        with Image.open(media.file_path) as img:
            filtered_img = FILTERS[filter_name](img)

            # Save filtered image
            filtered_path = f"{os.path.splitext(media.file_path)[0]}_{filter_name}.jpg"
            filtered_img.save(filtered_path, 'JPEG', quality=95)

            # Update media record or create new version
            # This could be implemented based on your requirements

        return jsonify({'success': True, 'filtered_path': filtered_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@media_bp.route('/add-sticker', methods=['POST'])
def add_sticker():
    """Add sticker to an image"""
    try:
        media_id = request.form.get('media_id')
        sticker_path = request.form.get('sticker_path')
        position_x = int(request.form.get('position_x', 0))
        position_y = int(request.form.get('position_y', 0))
        scale = float(request.form.get('scale', 1.0))

        media = Media.query.get_or_404(media_id)

        if media.file_type != 'image':
            return jsonify({'error': 'Only images can have stickers'}), 400

        # Open base image
        with Image.open(media.file_path) as base_img:
            # Open sticker image
            sticker_full_path = os.path.join(current_app.static_folder, 'images', 'stickers', sticker_path)
            with Image.open(sticker_full_path) as sticker_img:
                # Resize sticker
                new_size = (int(sticker_img.width * scale), int(sticker_img.height * scale))
                sticker_img = sticker_img.resize(new_size, Image.Resampling.LANCZOS)

                # Ensure sticker has alpha channel
                if sticker_img.mode != 'RGBA':
                    sticker_img = sticker_img.convert('RGBA')

                # Paste sticker onto base image
                base_img.paste(sticker_img, (position_x, position_y), sticker_img)

                # Save result
                stickered_path = f"{os.path.splitext(media.file_path)[0]}_sticker.jpg"
                base_img.save(stickered_path, 'JPEG', quality=95)

        return jsonify({'success': True, 'stickered_path': stickered_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500