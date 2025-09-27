import os
from app import app, db
from models import Media, Event


def fix_database_paths():
    with app.app_context():
        # Fix media paths
        media_items = Media.query.all()
        for media in media_items:
            if media.file_path:
                # Convert absolute path to relative
                if 'jemtech-event-hub\\uploads\\' in media.file_path:
                    relative_path = media.file_path.split('jemtech-event-hub\\uploads\\')[-1]
                    relative_path = relative_path.replace('\\', '/')
                    media.file_path = relative_path
                    print(f"Fixed media {media.id}: {relative_path}")

            if media.thumbnail_path:
                if 'jemtech-event-hub\\uploads\\' in media.thumbnail_path:
                    relative_path = media.thumbnail_path.split('jemtech-event-hub\\uploads\\')[-1]
                    relative_path = relative_path.replace('\\', '/')
                    media.thumbnail_path = relative_path
                    print(f"Fixed media thumb {media.id}: {relative_path}")

        # Fix event banner paths
        events = Event.query.all()
        for event in events:
            if event.banner_image and 'jemtech-event-hub\\uploads\\' in event.banner_image:
                relative_path = event.banner_image.split('jemtech-event-hub\\uploads\\')[-1]
                relative_path = relative_path.replace('\\', '/')
                event.banner_image = relative_path
                print(f"Fixed event banner {event.id}: {relative_path}")

        db.session.commit()
        print("Database paths fixed successfully!")


if __name__ == '__main__':
    fix_database_paths()