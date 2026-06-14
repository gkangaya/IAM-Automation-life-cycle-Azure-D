import logging
import sys

from flask import Flask
from flask_login import LoginManager
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Configure root logger to show everything
logging.basicConfig(
    level=logging.INFO,  # This will show INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Print to console
    ]
)

# Set specific loggers
logger = logging.getLogger(__name__)
logger.info("Application starting up...")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'warning'

# Initialize Azure AD helper
from .azure_ad_helper import AzureADHelper
app.azure_ad_helper = AzureADHelper()
app.azure_ad_helper.init_app(app)

# Import routes
from . import routes, auth_routes

logger.info("Application initialization complete")
