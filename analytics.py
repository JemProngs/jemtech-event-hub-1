from flask import Blueprint, send_file, jsonify, current_app
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
import numpy as np
from models import db, Event, Media, CheckIn, User
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import os

analytics_bp = Blueprint('analytics', __name__)

# Download VADER lexicon if not already available
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()


@analytics_bp.route('/event/<int:event_id>')
def event_analytics(event_id):
    """Generate analytics report for an event (Flask route)."""
    img_buffer = generate_event_report(event_id, save_to_file=True, return_buffer=True)
    return send_file(img_buffer, mimetype='image/png')


@analytics_bp.route('/dashboard')
def dashboard_analytics():
    """Generate overall dashboard analytics."""
    total_events = Event.query.count()
    total_users = User.query.count()
    total_media = Media.query.count()
    total_checkins = CheckIn.query.count()

    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()

    events_by_status = {
        'approved': Event.query.filter_by(status='approved').count(),
        'pending': Event.query.filter_by(status='pending').count(),
        'rejected': Event.query.filter_by(status='rejected').count()
    }

    media_by_type = {
        'image': Media.query.filter_by(file_type='image').count(),
        'video': Media.query.filter_by(file_type='video').count()
    }

    return jsonify({
        'total_events': total_events,
        'total_users': total_users,
        'total_media': total_media,
        'total_checkins': total_checkins,
        'events_by_status': events_by_status,
        'media_by_type': media_by_type,
        'recent_events': [
            {
                'id': event.id,
                'title': event.title,
                'status': event.status,
                'created_at': event.created_at.isoformat()
            } for event in recent_events
        ]
    })


def generate_checkins_chart(ax, checkin_times, start_time, end_time):
    """Generate chart showing check-ins over time."""
    if not checkin_times:
        ax.text(0.5, 0.5, 'No check-in data', ha='center', va='center')
        ax.set_title('Check-ins Over Time')
        return

    time_buckets = {}
    for checkin_time in checkin_times:
        hour = checkin_time.replace(minute=0, second=0, microsecond=0)
        time_buckets[hour] = time_buckets.get(hour, 0) + 1

    sorted_times = sorted(time_buckets.keys())
    counts = [time_buckets[time] for time in sorted_times]
    time_labels = [time.strftime('%H:%M') for time in sorted_times]

    ax.bar(range(len(counts)), counts, color=current_app.config['APP_THEME']['primary'])
    ax.set_title('Check-ins Over Time', fontweight='bold')
    ax.set_xlabel('Time')
    ax.set_ylabel('Number of Check-ins')
    ax.set_xticks(range(len(time_labels)))
    ax.set_xticklabels(time_labels, rotation=45, ha='right')


def generate_uploads_chart(ax, upload_times, start_time, end_time):
    """Generate chart showing uploads over time."""
    if not upload_times:
        ax.text(0.5, 0.5, 'No upload data', ha='center', va='center')
        ax.set_title('Uploads Over Time')
        return

    time_buckets = {}
    for upload_time in upload_times:
        hour = upload_time.replace(minute=0, second=0, microsecond=0)
        time_buckets[hour] = time_buckets.get(hour, 0) + 1

    sorted_times = sorted(time_buckets.keys())
    counts = [time_buckets[time] for time in sorted_times]
    time_labels = [time.strftime('%H:%M') for time in sorted_times]

    ax.plot(range(len(counts)), counts,
            marker='o',
            color=current_app.config['APP_THEME']['secondary'],
            linewidth=2)
    ax.fill_between(range(len(counts)), counts, alpha=0.3,
                    color=current_app.config['APP_THEME']['secondary'])
    ax.set_title('Uploads Over Time', fontweight='bold')
    ax.set_xlabel('Time')
    ax.set_ylabel('Number of Uploads')
    ax.set_xticks(range(len(time_labels)))
    ax.set_xticklabels(time_labels, rotation=45, ha='right')
    ax.grid(True, alpha=0.3)


def generate_status_chart(ax, status_counts):
    """Generate pie chart of media status distribution."""
    if not any(status_counts.values()):
        ax.text(0.5, 0.5, 'No status data', ha='center', va='center')
        ax.set_title('Media Status Distribution')
        return

    labels = list(status_counts.keys())
    sizes = list(status_counts.values())
    colors = [
        current_app.config['APP_THEME']['success'],
        current_app.config['APP_THEME']['warning'],
        current_app.config['APP_THEME']['danger']
    ]

    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                      colors=colors, startangle=90)

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    ax.axis('equal')
    ax.set_title('Media Status Distribution', fontweight='bold')


def generate_engagement_chart(ax, event, media, checkins):
    """Generate engagement metrics chart."""
    metrics = {
        'Total Media': len(media),
        'Approved Media': len([m for m in media if m.status == 'approved']),
        'Total Check-ins': len(checkins),
        'Active Participants': len(set([c.session_id for c in checkins])) if checkins else 0,
        'Average Likes': sum(m.likes for m in media) / len(media) if media else 0
    }

    if not any(metrics.values()):
        ax.text(0.5, 0.5, 'No engagement data', ha='center', va='center')
        ax.set_title('Engagement Metrics')
        return

    labels = list(metrics.keys())
    values = list(metrics.values())
    y_pos = np.arange(len(labels))

    bars = ax.barh(y_pos, values,
                   color=current_app.config['APP_THEME']['info'])

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel('Count')
    ax.set_title('Engagement Metrics', fontweight='bold')

    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f'{values[i]:.1f}', ha='left', va='center')

    ax.grid(True, alpha=0.3, axis='x')


def generate_event_report(event_id, save_to_file=True, return_buffer=False):
    """Generate analytics report for a given event."""
    event = Event.query.get_or_404(event_id)
    checkins = CheckIn.query.filter_by(event_id=event_id).all()
    media = Media.query.filter_by(event_id=event_id).all()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'Analytics Report for {event.title}', fontsize=16)

    # 1. Check-ins
    if checkins:
        checkin_times = [c.checked_in_at for c in checkins]
        generate_checkins_chart(ax1, checkin_times, event.start_date, event.end_date)
    else:
        ax1.text(0.5, 0.5, 'No check-in data', ha='center', va='center')
        ax1.set_title('Check-ins Over Time')

    # 2. Uploads
    if media:
        upload_times = [m.created_at for m in media]
        generate_uploads_chart(ax2, upload_times, event.start_date, event.end_date)
    else:
        ax2.text(0.5, 0.5, 'No upload data', ha='center', va='center')
        ax2.set_title('Uploads Over Time')

    # 3. Media Status
    if media:
        status_counts = {
            'Approved': len([m for m in media if m.status == 'approved']),
            'Pending': len([m for m in media if m.status == 'pending']),
            'Rejected': len([m for m in media if m.status == 'rejected'])
        }
        generate_status_chart(ax3, status_counts)
    else:
        ax3.text(0.5, 0.5, 'No media data', ha='center', va='center')
        ax3.set_title('Media Status Distribution')

    # 4. Engagement
    generate_engagement_chart(ax4, event, media, checkins)

    plt.tight_layout()

    if save_to_file:
        reports_dir = current_app.config['REPORT_FOLDER']
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(
            reports_dir,
            f'report_{event_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.png'
        )
        plt.savefig(report_path, dpi=100, bbox_inches='tight')
    else:
        report_path = None

    # Always create buffer if requested
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    plt.close(fig)

    if return_buffer:
        return buffer
    return report_path
