from flask import Blueprint, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
import json
from models import db, Collage, CollageTemplate, Event, Media
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from io import BytesIO

collage_bp = Blueprint('collage', __name__)

# Predefined collage templates
TEMPLATES = {
    'basic_2x2': {
        'name': '2x2 Grid',
        'layout': [
            {'x': 0, 'y': 0, 'width': 0.5, 'height': 0.5},
            {'x': 0.5, 'y': 0, 'width': 0.5, 'height': 0.5},
            {'x': 0, 'y': 0.5, 'width': 0.5, 'height': 0.5},
            {'x': 0.5, 'y': 0.5, 'width': 0.5, 'height': 0.5}
        ],
        'thumbnail': 'collage_2x2.jpg'
    },
    'vertical_split': {
        'name': 'Vertical Split',
        'layout': [
            {'x': 0, 'y': 0, 'width': 0.5, 'height': 1.0},
            {'x': 0.5, 'y': 0, 'width': 0.5, 'height': 1.0}
        ],
        'thumbnail': 'collage_vertical.jpg'
    },
    'horizontal_split': {
        'name': 'Horizontal Split',
        'layout': [
            {'x': 0, 'y': 0, 'width': 1.0, 'height': 0.5},
            {'x': 0, 'y': 0.5, 'width': 1.0, 'height': 0.5}
        ],
        'thumbnail': 'collage_horizontal.jpg'
    },
    'main_with_sides': {
        'name': 'Main with Sides',
        'layout': [
            {'x': 0, 'y': 0, 'width': 0.3, 'height': 1.0},
            {'x': 0.3, 'y': 0, 'width': 0.4, 'height': 1.0},
            {'x': 0.7, 'y': 0, 'width': 0.3, 'height': 1.0}
        ],
        'thumbnail': 'collage_main_sides.jpg'
    }
}


@collage_bp.route('/templates')
def list_templates():
    """Get available collage templates"""
    return jsonify({
        'templates': TEMPLATES,
        'categories': ['all', 'wedding', 'birthday', 'corporate', 'casual']
    })


@collage_bp.route('/create', methods=['POST'])
def create_collage():
    """Create a collage from selected images"""
    try:
        event_id = request.form.get('event_id')
        template_name = request.form.get('template')
        image_ids = request.form.getlist('image_ids')
        title = request.form.get('title', '')

        if not event_id or not template_name or not image_ids:
            return jsonify({'error': 'Missing required parameters'}), 400

        event = Event.query.get_or_404(event_id)

        # Get template
        template = TEMPLATES.get(template_name)
        if not template:
            return jsonify({'error': 'Invalid template'}), 400

        # Get images
        images = []
        for img_id in image_ids:
            media = Media.query.get(img_id)
            if media and media.status == 'approved':
                images.append(media.file_path)

        if len(images) < len(template['layout']):
            return jsonify({'error': 'Not enough images for this template'}), 400

        # Create collage
        collage_path = generate_collage_image(images, template, title, event_id)

        # Save to database
        collage = Collage(
            event_id=event_id,
            title=title,
            config_data=json.dumps({
                'template': template_name,
                'image_ids': image_ids,
                'created_at': datetime.utcnow().isoformat()
            }),
            output_path=collage_path
        )

        db.session.add(collage)
        db.session.commit()

        return jsonify({
            'success': True,
            'collage_id': collage.id,
            'collage_path': collage_path
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def generate_collage_image(image_paths, template, title, event_id):
    """Generate a collage image from the template and images"""
    # Create output directory
    output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'collages', str(event_id))
    os.makedirs(output_dir, exist_ok=True)

    # Base image size
    width, height = 1200, 800

    # Create base image
    base_image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(base_image)

    # Add title if provided
    if title:
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            font = ImageFont.load_default()

        # Draw title background
        title_bg_height = 60
        draw.rectangle([(0, 0), (width, title_bg_height)], fill=(0, 94, 184))  # JemTech blue

        # Draw title text
        draw.text((width // 2, title_bg_height // 2), title, fill=(255, 255, 255),
                  font=font, anchor="mm")

    # Calculate content area (below title)
    content_top = 70 if title else 0
    content_height = height - content_top

    # Place images according to template
    for i, slot in enumerate(template['layout']):
        if i < len(image_paths):
            try:
                with Image.open(image_paths[i]) as img:
                    # Calculate position and size
                    slot_x = int(slot['x'] * width)
                    slot_y = content_top + int(slot['y'] * content_height)
                    slot_width = int(slot['width'] * width)
                    slot_height = int(slot['height'] * content_height)

                    # Resize image to fit slot
                    img.thumbnail((slot_width, slot_height), Image.Resampling.LANCZOS)

                    # Calculate position to center image in slot
                    img_x = slot_x + (slot_width - img.width) // 2
                    img_y = slot_y + (slot_height - img.height) // 2

                    # Paste image
                    base_image.paste(img, (img_x, img_y))
            except Exception as e:
                current_app.logger.error(f"Error processing image {image_paths[i]}: {e}")
                # Draw error placeholder
                draw.rectangle([(slot_x, slot_y),
                                (slot_x + slot_width, slot_y + slot_height)],
                               fill=(200, 200, 200))
                draw.text((slot_x + slot_width // 2, slot_y + slot_height // 2),
                          "Image Error", fill=(100, 100, 100), anchor="mm")

    # Add watermark
    watermark_text = f"JemTech Event Hub - {datetime.utcnow().strftime('%Y-%m-%d')}"
    try:
        watermark_font = ImageFont.truetype("arial.ttf", 12)
    except:
        watermark_font = ImageFont.load_default()

    watermark_bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
    watermark_width = watermark_bbox[2] - watermark_bbox[0]
    watermark_height = watermark_bbox[3] - watermark_bbox[1]

    draw.text((width - watermark_width - 10, height - watermark_height - 10),
              watermark_text, fill=(150, 150, 150), font=watermark_font)

    # Save collage
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"collage_{timestamp}.jpg"
    output_path = os.path.join(output_dir, filename)

    base_image.save(output_path, 'JPEG', quality=95)

    return output_path


@collage_bp.route('/download/<int:collage_id>')
def download_collage(collage_id):
    """Download collage as PDF"""
    collage = Collage.query.get_or_404(collage_id)

    # Create PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Add title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, collage.title or "Event Collage")

    # Add collage image
    if os.path.exists(collage.output_path):
        img = ImageReader(collage.output_path)
        img_width, img_height = img.getSize()

        # Scale image to fit page
        max_width = width - 100
        max_height = height - 150

        scale = min(max_width / img_width, max_height / img_height)
        new_width = img_width * scale
        new_height = img_height * scale

        # Center image
        x = (width - new_width) / 2
        y = height - new_height - 100

        c.drawImage(img, x, y, width=new_width, height=new_height)

    # Add footer
    c.setFont("Helvetica", 10)
    c.drawString(50, 30, f"Created on {collage.created_at.strftime('%Y-%m-%d %H:%M')}")
    c.drawString(width - 200, 30, "JemTech Event Hub")

    c.save()
    buffer.seek(0)

    filename = f"collage_{collage.id}.pdf"
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


@collage_bp.route('/preview/<int:collage_id>')
def preview_collage(collage_id):
    """Preview collage image"""
    collage = Collage.query.get_or_404(collage_id)

    if not os.path.exists(collage.output_path):
        return jsonify({'error': 'Collage file not found'}), 404

    return send_file(collage.output_path, mimetype='image/jpeg')