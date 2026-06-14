import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Azure AD Configuration for Graph API
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
    AZURE_TENANT_DOMAIN = os.environ.get('AZURE_TENANT_DOMAIN')
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')

    # Azure AD OAuth Configuration for SSO
    AZURE_OAUTH_CLIENT_ID = os.environ.get('AZURE_OAUTH_CLIENT_ID', os.environ.get('AZURE_CLIENT_ID'))
    AZURE_OAUTH_CLIENT_SECRET = os.environ.get('AZURE_OAUTH_CLIENT_SECRET', os.environ.get('AZURE_CLIENT_SECRET'))
    AZURE_OAUTH_TENANT_ID = os.environ.get('AZURE_TENANT_ID', 'common')  # 'common' for multi-tenant, or your tenant ID
    AZURE_OAUTH_REDIRECT_URI = os.environ.get('AZURE_OAUTH_REDIRECT_URI', 'http://localhost:5000/auth/callback')

    # Microsoft Graph API endpoints
    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    AUTHORITY = f'https://login.microsoftonline.com/{AZURE_TENANT_ID}'
    OATH_AUTHORITY = f'https://login.microsoftonline.com/{AZURE_OAUTH_TENANT_ID}'
    SCOPE = ['https://graph.microsoft.com/.default']
    OATH_SCOPES = [
        'User.Read',  # Read user profile
        'Directory.Read.All'  # Read directory information
    ]

    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # Allowed admin users (email addresses or user principal names)
    ALLOWED_ADMINS = os.environ.get('ALLOWED_ADMINS', '').split(',')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')