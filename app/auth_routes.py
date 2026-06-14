from datetime import datetime

from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from . import app, login_manager
from .forms import LoginForm, ChangePasswordForm
from .models import AdminUser, LoginAttempt
import logging
from datetime import datetime

from .oauth import AzureOAuth

logger = logging.getLogger(__name__)

# Initialize OAuth
oauth = AzureOAuth()
oauth.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    """Load user from session"""
    # For OAuth, we don't need to reload from database
    # The user info is stored in the session
    if 'user_info' in session:
        return AdminUser(session['user_info'])
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access"""
    logger.warning(f"Unauthorized access to {request.path}")
    flash('Please log in to access this page', 'warning')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with Microsoft SSO option"""
    # If already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    client_ip = request.remote_addr

    # Check for lockout
    if LoginAttempt.is_locked_out(client_ip):
        flash('Too many failed attempts. Please try again later.', 'error')
        return render_template('login.html', form=form)

    # Handle form login (legacy)
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        logger.info(f"Legacy login attempt for {username}")

        # For legacy login, you can still support local admin
        # But we'll redirect to OAuth
        flash('Please use Sign in with Microsoft for secure access', 'info')
        return redirect(url_for('microsoft_login'))

    return render_template('login.html', form=form)

@app.route('/auth/microsoft/login')
def microsoft_login():
    """Initiate Microsoft OAuth login"""
    logger.info(f"Microsoft login initiated from IP: {request.remote_addr}")
    login_url = oauth.get_login_url()
    print(login_url)
    return redirect(login_url)

@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Microsoft"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')


    if error:
        logger.error(f"OAuth error: {error}")
        flash(f'Authentication failed: {error}', 'error')
        return redirect(url_for('login'))

    if not code:
        flash('Authentication failed: No authorization code received', 'error')
        return redirect(url_for('login'))

    # Process the OAuth callback
    user_info, error_msg = oauth.handle_callback(code, state)

    if error_msg or not user_info:
        logger.error(f"OAuth callback failed: {error_msg}")
        flash(f'Authentication failed: {error_msg}', 'error')
        return redirect(url_for('login'))

    # Check if user is authorized as admin
    if not oauth.is_authorized_admin(user_info):
        logger.warning(f"Unauthorized user attempted login: {user_info.get('username')}")
        flash('You are not authorized to access this portal', 'error')
        return redirect(url_for('login'))

    # Successful authentication
    logger.info(f"Successful Microsoft login for {user_info.get('username')}")

    # Create user session
    user = AdminUser.from_oauth(user_info)
    login_user(user, remember=True)

    # Store user info in session
    session['user_info'] = user_info
    session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    session['login_ip'] = request.remote_addr
    session['login_method'] = 'microsoft_sso'

    # Reset login attempts
    LoginAttempt.reset_attempts(request.remote_addr)

    flash(f'Welcome {user_info.get("display_name", user_info.get("username"))}!', 'success')

    # Redirect to next page or dashboard
    next_page = request.args.get('next')
    if next_page and next_page.startswith('/'):
        return redirect(next_page)
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logger.info(f"User {current_user.username} logging out")

    # Clear session
    session.clear()
    logout_user()

    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/auth/microsoft/logout')
def microsoft_logout():
    """Logout from Microsoft as well"""
    logout_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/logout"
    return redirect(logout_url)