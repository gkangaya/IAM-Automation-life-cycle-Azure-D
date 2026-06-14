import requests
from msal import ConfidentialClientApplication
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class AzureADHelper:
    def __init__(self):
        self.app = None

    def init_app(self, app):
        self.app = app
        self.client_app = ConfidentialClientApplication(
            client_id=app.config['AZURE_CLIENT_ID'],
            client_credential=app.config['AZURE_CLIENT_SECRET'],
            authority=app.config['AUTHORITY']
        )

    def get_access_token(self):
        """Get access token for Microsoft Graph API"""
        result = self.client_app.acquire_token_for_client(scopes=current_app.config['SCOPE'])

        if 'access_token' in result:
            return result['access_token']
        else:
            logger.error(f"Failed to get access token: {result.get('error_description')}")
            raise Exception("Failed to authenticate with Azure AD")

    def create_user(self, user_data):
        """Create a new user in Azure AD"""
        token = self.get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Prepare user payload
        user_payload = {
            "accountEnabled": True,
            "displayName": user_data['display_name'],
            "mailNickname": user_data['username'],
            "userPrincipalName": f"{user_data['username']}@{current_app.config['AZURE_TENANT_DOMAIN']}",
            "passwordProfile": {
                "forceChangePasswordNextSignIn": True,
                "password": user_data['password']
            }
        }

        # Add optional fields
        if user_data.get('given_name'):
            user_payload['givenName'] = user_data['given_name']
        if user_data.get('surname'):
            user_payload['surname'] = user_data['surname']
        if user_data.get('job_title'):
            user_payload['jobTitle'] = user_data['job_title']
        if user_data.get('department'):
            user_payload['department'] = user_data['department']

        response = requests.post(
            f"{current_app.config['GRAPH_API_ENDPOINT']}/users",
            headers=headers,
            json=user_payload
        )

        if response.status_code == 201:
            logger.info(f"User {user_data['username']} created successfully")
            return response.json()
        else:
            logger.error(f"Failed to create user: {response.text}")
            raise Exception(f"Azure AD API error: {response.text}")

    def get_users(self, top=100):
        """Get list of users from Azure AD"""
        logger.info(f"Fetching up to {top} users...")

        token = self.get_access_token()
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.get(
            f"{current_app.config['GRAPH_API_ENDPOINT']}/users?$top={top}&$select=id,displayName,userPrincipalName,mail,givenName,surname,jobTitle,department,accountEnabled,createdDateTime",
            headers=headers
        )

        if response.status_code == 200:
            users = response.json().get('value', [])
            logger.info(f"Retrieved {len(users)} users")
            return users
        else:
            logger.error(f"Failed to get users: {response.text}")
            raise Exception("Failed to retrieve users")

    def get_user(self, user_id):
        """Get specific user details"""
        logger.info(f"Fetching user: {user_id}")

        token = self.get_access_token()
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.get(
            f"{current_app.config['GRAPH_API_ENDPOINT']}/users/{user_id}",
            headers=headers
        )

        if response.status_code == 200:
            logger.info(f"User {user_id} found")
            return response.json()
        else:
            logger.warning(f"User {user_id} not found")
            return None

    def update_user(self, user_id, user_data):
        """Update user in Azure AD"""
        logger.info(f"Updating user: {user_id}")

        token = self.get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        update_payload = {}
        if user_data.get('display_name'):
            update_payload['displayName'] = user_data['display_name']
        if user_data.get('given_name'):
            update_payload['givenName'] = user_data['given_name']
        if user_data.get('surname'):
            update_payload['surname'] = user_data['surname']
        if user_data.get('job_title'):
            update_payload['jobTitle'] = user_data['job_title']
        if user_data.get('department'):
            update_payload['department'] = user_data['department']

        response = requests.patch(
            f"{current_app.config['GRAPH_API_ENDPOINT']}/users/{user_id}",
            headers=headers,
            json=update_payload
        )

        if response.status_code == 204:
            logger.info(f"User {user_id} updated successfully")
            return True
        else:
            logger.error(f"Failed to update user: {response.text}")
            raise Exception(f"Azure AD API error: {response.text}")

    def delete_user(self, user_id):
        """Delete user from Azure AD"""
        logger.warning(f"Deleting user: {user_id}")

        token = self.get_access_token()
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.delete(
            f"{current_app.config['GRAPH_API_ENDPOINT']}/users/{user_id}",
            headers=headers
        )

        if response.status_code == 204:
            logger.info(f"User {user_id} deleted successfully")
            return True
        else:
            logger.error(f"Failed to delete user: {response.text}")
            raise Exception(f"Azure AD API error: {response.text}")

    def enable_disable_user(self, user_id, enable=True):
        """Enable or disable user account"""
        action = "enable" if enable else "disable"
        logger.info(f"{action.capitalize()}ing user: {user_id}")

        token = self.get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        payload = {"accountEnabled": enable}

        response = requests.patch(
            f"{current_app.config['GRAPH_API_ENDPOINT']}/users/{user_id}",
            headers=headers,
            json=payload
        )

        if response.status_code == 204:
            logger.info(f"User {user_id} {action}d")
            return True
        else:
            logger.error(f"Failed to {action} user")
            return False

    def get_users_by_department(self, department):
        """Get all users in a specific department"""
        token = self.get_access_token()
        headers = {'Authorization': f'Bearer {token}'}

        filter_query = f"department eq '{department}'"
        response = requests.get(
            f"{current_app.config['GRAPH_API_ENDPOINT']}/users?$filter={filter_query}&$select=id,displayName,userPrincipalName,mail,jobTitle,department",
            headers=headers
        )

        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            logger.error(f"Failed to get users by department: {response.text}")
            return []

    def get_department_stats(self):
        """Get statistics about departments"""
        users = self.get_users(top=999)
        stats = {}

        for user in users:
            dept = user.get('department')
            if dept:
                if dept not in stats:
                    stats[dept] = 0
                stats[dept] += 1

        return stats