from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_mail import Mail, Message
from flask_wtf.csrf import validate_csrf
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import bcrypt

from models import db, User
from config import Config

# Blueprint & Extensions
auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()
mail = Mail()
serializer = URLSafeTimedSerializer(Config.SECRET_KEY)


# ====================
# User Loader
# ====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ====================
# Login
# ====================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        try:
            # Validate CSRF token
            validate_csrf(request.form.get('csrf_token'))

            username = request.form.get('username')
            password = request.form.get('password')
            remember_me = bool(request.form.get('remember_me'))

            user = User.query.filter_by(username=username).first()

            if (
                user
                and user.password_hash
                and bcrypt.checkpw(password.encode('utf-8'),
                                   user.password_hash.encode('utf-8'))
                and user.is_active
            ):
                login_user(user, remember=remember_me)
                user.last_login = datetime.now()
                db.session.commit()

                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                if user.is_admin:
                    return redirect(next_page or url_for('admin_dashboard'))
                return redirect(next_page or url_for('user_dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Invalid request. Please try again.', 'danger')

    return render_template('auth/login.html')


# ====================
# Register
# ====================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        # Hash password with bcrypt
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), salt
        ).decode('utf-8')

        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name
        )

        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# ====================
# Logout
# ====================
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ====================
# Forgot Password
# ====================
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate reset token
            token = serializer.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password',
                                token=token, _external=True)

            # Send email
            msg = Message(
                subject='Password Reset Request',
                recipients=[user.email],
                html=render_template(
                    'email/password_reset.html',
                    user=user, reset_url=reset_url
                )
            )
            mail.send(msg)

        flash(
            'If an account with that email exists, '
            'a password reset link has been sent.',
            'info'
        )
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot-password.html')


# ====================
# Reset Password
# ====================
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(
            token, salt='password-reset-salt', max_age=3600
        )  # 1 hour expiry
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Invalid or expired reset token.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if request.method == 'POST':
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template(
                    'auth/reset_password.html', token=token
                )

            # Update password with bcrypt
            salt = bcrypt.gensalt()
            user.password_hash = bcrypt.hashpw(
                password.encode('utf-8'), salt
            ).decode('utf-8')
            db.session.commit()

            flash('Password has been reset successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))

        return render_template('auth/reset_password.html', token=token)

    except Exception:
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
