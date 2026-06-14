import requests
from urllib.parse import quote, urlencode
from flask import current_app, session, redirect, url_for
from msal import ConfidentialClientApplication
import logging

logger = logging.getLogger(__name__)


class AzureOAuth:
    """Handle Microsoft OAuth authentication"""

    def __init__(self):
        self.app = None

    def init_app(self, app):
        self.app = app
        self.client_app = ConfidentialClientApplication(
            client_id=app.config['AZURE_OAUTH_CLIENT_ID'],
            client_credential=app.config['AZURE_OAUTH_CLIENT_SECRET'],
            authority=app.config['OATH_AUTHORITY']
        )
        logger.info("Azure OAuth initialized")

    def get_login_url(self, redirect_uri=None):
        """Get Microsoft login URL"""
        if not redirect_uri:
            redirect_uri = current_app.config['AZURE_OAUTH_REDIRECT_URI']

        # Generate a random state parameter for CSRF protection
        import secrets
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state

        # Build the authorization URL
        params = {
            'client_id': current_app.config['AZURE_OAUTH_CLIENT_ID'],
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(current_app.config['OATH_SCOPES']),
            # 'scope':  "openid profile offline_access",
            'state': state,
            'response_mode': 'query'
        }

        auth_url = f"{current_app.config['OATH_AUTHORITY']}/oauth2/v2.0/authorize?" + urlencode(params)
        logger.info(f"Generated OAuth login URL")
        return auth_url

    def handle_callback(self, code, state, redirect_uri=None):
        """Handle OAuth callback and get user info"""
        # Verify state to prevent CSRF
        saved_state = session.get('oauth_state')
        if not saved_state or saved_state != state:
            logger.error(f"OAuth state mismatch. Expected: {saved_state}, Got: {state}")
            return None, "Invalid state parameter"

        if not redirect_uri:
            redirect_uri = current_app.config['AZURE_OAUTH_REDIRECT_URI']

        # Exchange code for token
        try:
            token_result = self.client_app.acquire_token_by_authorization_code(
                code=code,
                scopes=current_app.config['OATH_SCOPES'],
                redirect_uri=redirect_uri
            )

            if 'access_token' not in token_result:
                logger.error(f"Failed to get token: {token_result.get('error_description')}")
                return None, token_result.get('error_description', 'Authentication failed')

            # Get user info from Microsoft Graph
            headers = {'Authorization': f"Bearer {token_result['access_token']}"}
            user_response = requests.get(
                f"{current_app.config['GRAPH_API_ENDPOINT']}/me",
                headers=headers
            )

            if user_response.status_code != 200:
                logger.error(f"Failed to get user info: {user_response.text}")
                return None, "Failed to get user information"

            user_info = user_response.json()

            # Also get directory roles if needed
            roles_response = requests.get(
                f"{current_app.config['GRAPH_API_ENDPOINT']}/me/memberOf",
                headers=headers
            )

            user_roles = []
            if roles_response.status_code == 200:
                user_roles = roles_response.json().get('value', [])

            logger.info(f"Successfully authenticated user: {user_info.get('userPrincipalName')}")

            return {
                'id': user_info.get('id'),
                'username': user_info.get('userPrincipalName'),
                'email': user_info.get('mail', user_info.get('userPrincipalName')),
                'display_name': user_info.get('displayName'),
                'given_name': user_info.get('givenName'),
                'surname': user_info.get('surname'),
                'roles': user_roles
            }, None

        except Exception as e:
            logger.error(f"OAuth callback error: {str(e)}")
            return None, str(e)

    def is_authorized_admin(self, user_info):
        """Check if user is authorized as admin"""
        allowed_admins = current_app.config.get('ALLOWED_ADMINS', [])

        # If no allowed admins configured, allow all authenticated users
        if not allowed_admins or allowed_admins == ['']:
            logger.warning("No allowed admins configured - allowing all authenticated users")
            return True

        # Check if user's email or UPN is in allowed list
        user_email = user_info.get('email', '').lower()
        user_upn = user_info.get('username', '').lower()

        for admin in allowed_admins:
            admin = admin.strip().lower()
            if admin and (admin == user_email or admin == user_upn):
                logger.info(f"User {user_upn} is authorized as admin")
                return True

        logger.warning(f"User {user_upn} is not in allowed admins list: {allowed_admins}")
        return False