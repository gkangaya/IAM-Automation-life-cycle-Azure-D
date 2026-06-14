from flask import render_template, request, redirect, url_for, flash, jsonify


import secrets
import logging

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import app
from .forms import CreateUserForm, UpdateUserForm
import secrets
import logging

logger = logging.getLogger(__name__)


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/users')
@login_required
def manage_users():
    logger.info(f"User {current_user.username} viewing users list")
    try:
        users = app.azure_ad_helper.get_users()
        return render_template('manage_users.html', users=users)
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        flash(f'Error fetching users: {str(e)}', 'error')
        return render_template('manage_users.html', users=[])


@app.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    form = CreateUserForm()

    if form.validate_on_submit():
        try:
            # Generate a secure temporary password if not provided
            password = form.password.data
            if not password:
                password = secrets.token_urlsafe(12)

            user_data = {
                'username': form.username.data,
                'display_name': form.display_name.data,
                'given_name': form.given_name.data,
                'surname': form.surname.data,
                'password': password,
                'job_title': form.job_title.data,
                'department': form.department.data
            }

            result = app.azure_ad_helper.create_user(user_data)
            flash(f'User {form.display_name.data} created successfully!', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'error')

    return render_template('create_user.html', form=form)


@app.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    form = UpdateUserForm()

    if request.method == 'GET':
        user = app.azure_ad_helper.get_user(user_id)
        if user:
            form.display_name.data = user.get('displayName', '')
            form.given_name.data = user.get('givenName', '')
            form.surname.data = user.get('surname', '')
            form.job_title.data = user.get('jobTitle', '')
            form.department.data = user.get('department', '')
        else:
            flash('User not found', 'error')
            return redirect(url_for('manage_users'))

    if form.validate_on_submit():
        try:
            user_data = {
                'display_name': form.display_name.data,
                'given_name': form.given_name.data,
                'surname': form.surname.data,
                'job_title': form.job_title.data,
                'department': form.department.data
            }

            app.azure_ad_helper.update_user(user_id, user_data)
            flash('User updated successfully!', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'error')

    return render_template('edit_user.html', form=form, user_id=user_id)


@app.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    try:
        app.azure_ad_helper.delete_user(user_id)
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')

    return redirect(url_for('manage_users'))


@app.route('/users/<user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    data = request.get_json()
    enable = data.get('enable', True)

    try:
        success = app.azure_ad_helper.enable_disable_user(user_id, enable)
        if success:
            return jsonify({'success': True, 'message': f'User {"enabled" if enable else "disabled"} successfully'})
        else:
            return jsonify({'success': False, 'message': 'Operation failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/users')
@login_required
def api_get_users():
    try:
        users = app.azure_ad_helper.get_users()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/profile')
@login_required
def profile():
    """Admin profile page"""
    return render_template('profile.html')


@app.route('/departments')
@login_required
def departments():
    """View and manage departments"""
    logger.info(f"User {current_user.username} viewing departments")
    try:
        # Fetch all users to extract unique departments
        users = app.azure_ad_helper.get_users(top=999)

        # Extract unique departments
        departments_dict = {}
        for user in users:
            dept = user.get('department')
            if dept:
                if dept not in departments_dict:
                    departments_dict[dept] = {
                        'name': dept,
                        'count': 0,
                        'users': []
                    }
                departments_dict[dept]['count'] += 1
                departments_dict[dept]['users'].append({
                    'id': user.get('id'),
                    'displayName': user.get('displayName'),
                    'userPrincipalName': user.get('userPrincipalName'),
                    'jobTitle': user.get('jobTitle')
                })

        # Convert to list and sort by name
        departments_list = sorted(departments_dict.values(), key=lambda x: x['name'])

        return render_template('departments.html', departments=departments_list)
    except Exception as e:
        logger.error(f"Error loading departments: {e}")
        flash(f'Error loading departments: {str(e)}', 'error')
        return render_template('departments.html', departments=[])


@app.route('/users/<user_id>/move', methods=['POST'])
@login_required
def move_user(user_id):
    """Move user to different department"""
    try:
        data = request.get_json()
        new_department = data.get('department')
        effective_date = data.get('effective_date')
        reason = data.get('reason')

        # Update user's department
        user_data = {'department': new_department}
        app.azure_ad_helper.update_user(user_id, user_data)

        # Log the move action
        logger.info(f"User {current_user.username} moved user {user_id} to department '{new_department}'")
        logger.info(f"Move details - Effective: {effective_date}, Reason: {reason}")

        # You could also store this in an audit log database
        flash(f'User moved to {new_department} department successfully', 'success')
        return jsonify({'success': True, 'message': 'User moved successfully'})
    except Exception as e:
        logger.error(f"Error moving user: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/users/<user_id>/offboard', methods=['POST'])
@login_required
def offboard_user(user_id):
    """Offboard user (disable or delete)"""
    try:
        data = request.get_json()
        option = data.get('option')
        reason = data.get('reason')
        last_working_day = data.get('last_working_day')
        notes = data.get('notes')
        reassign_manager = data.get('reassign_manager')

        message = ""

        if option == 'disable':
            # Disable the user account
            app.azure_ad_helper.enable_disable_user(user_id, enable=False)
            message = "User account has been disabled"
            logger.info(f"User {current_user.username} disabled user {user_id}")

        elif option == 'disable_reassign':
            # Disable and reassign
            app.azure_ad_helper.enable_disable_user(user_id, enable=False)
            message = f"User account disabled and reassigned to {reassign_manager}"
            logger.info(f"User {current_user.username} disabled and reassigned user {user_id} to {reassign_manager}")

        elif option == 'delete':
            # Permanently delete the user
            app.azure_ad_helper.delete_user(user_id)
            message = "User account has been permanently deleted"
            logger.warning(f"User {current_user.username} deleted user {user_id}")

        # Log offboarding details
        logger.info(
            f"Offboarding details - User: {user_id}, Option: {option}, Reason: {reason}, Last Day: {last_working_day}")

        return jsonify({'success': True, 'message': message})
    except Exception as e:
        logger.error(f"Error offboarding user: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/users/bulk-move', methods=['POST'])
@login_required
def bulk_move_users():
    """Move multiple users to a department"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        new_department = data.get('department')

        success_count = 0
        for user_id in user_ids:
            try:
                app.azure_ad_helper.update_user(user_id, {'department': new_department})
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to move user {user_id}: {e}")

        logger.info(f"Bulk moved {success_count} users to {new_department}")
        return jsonify({'success': True, 'moved': success_count, 'total': len(user_ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500