from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)


class AdminUser(UserMixin):
    """Admin user model for authentication"""

    def __init__(self, user_info):
        self.id = user_info.get('id')
        self.username = user_info.get('username')
        self.email = user_info.get('email')
        self.display_name = user_info.get('display_name')
        self.given_name = user_info.get('given_name')
        self.surname = user_info.get('surname')

    def get_id(self):
        return self.id

    @staticmethod
    def validate_login(username, password):
        """Validate admin credentials"""
        from flask import current_app

        logger.info(f"Validating login for user: {username}")

        # Check if username matches
        if username != current_app.config['ADMIN_USERNAME']:
            logger.warning(f"Username mismatch: expected {current_app.config['ADMIN_USERNAME']}, got {username}")
            return False

        # Try password hash first
        password_hash = current_app.config.get('ADMIN_PASSWORD_HASH')
        if password_hash:
            try:
                logger.debug("Attempting to validate with password hash")
                is_valid = check_password_hash(password_hash, password)
                if is_valid:
                    logger.info("Password validation successful with hash")
                    return True
                else:
                    logger.warning("Password hash validation failed")
            except Exception as e:
                logger.error(f"Error checking password hash: {e}")

        # Fallback to plain text password (for development)
        expected_password = current_app.config.get('ADMIN_PASSWORD')
        if expected_password:
            logger.debug("Attempting fallback validation with plain text password")
            is_valid = password == expected_password
            if is_valid:
                logger.info("Password validation successful with plain text")
                return True
            else:
                logger.warning("Plain text password validation failed")

        logger.error(f"All validation methods failed for user {username}")
        return False

    @staticmethod
    def from_oauth(user_info):
        """Create AdminUser from OAuth user info"""
        return AdminUser(user_info)


class LoginAttempt:
    """Track login attempts for rate limiting"""

    _attempts = {}  # IP -> list of timestamps

    @classmethod
    def is_locked_out(cls, ip_address):
        """Check if IP is locked out"""
        from flask import current_app

        if ip_address not in cls._attempts:
            return False

        # Clean old attempts
        current_time = time.time()
        lockout_period = current_app.config.get('LOCKOUT_TIME_MINUTES', 15) * 60
        cls._attempts[ip_address] = [
            t for t in cls._attempts[ip_address]
            if current_time - t < lockout_period
        ]

        # Check if locked out
        limit = current_app.config.get('LOGIN_ATTEMPTS_LIMIT', 5)
        if len(cls._attempts[ip_address]) >= limit:
            # Check if still within lockout period
            oldest_attempt = min(cls._attempts[ip_address])
            if current_time - oldest_attempt < lockout_period:
                logger.warning(f"IP {ip_address} is locked out")
                return True
            else:
                # Reset attempts if lockout period passed
                cls._attempts[ip_address] = []

        return False

    @classmethod
    def add_attempt(cls, ip_address):
        """Add failed login attempt"""
        if ip_address not in cls._attempts:
            cls._attempts[ip_address] = []

        cls._attempts[ip_address].append(time.time())
        logger.info(f"Failed login attempt recorded for IP {ip_address}")

    @classmethod
    def reset_attempts(cls, ip_address):
        """Reset login attempts on successful login"""
        if ip_address in cls._attempts:
            del cls._attempts[ip_address]
            logger.info(f"Login attempts reset for IP {ip_address}")