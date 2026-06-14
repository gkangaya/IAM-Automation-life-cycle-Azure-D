import re

from flask_wtf import FlaskForm
from werkzeug.routing import ValidationError
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
import re

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    display_name = StringField('Display Name', validators=[
        DataRequired(),
        Length(max=128)
    ])
    given_name = StringField('First Name', validators=[Length(max=64)])
    surname = StringField('Last Name', validators=[Length(max=64)])
    email = StringField('Email', validators=[Optional(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    job_title = StringField('Job Title', validators=[Length(max=128)])
    department = StringField('Department', validators=[Length(max=128)])

class UpdateUserForm(FlaskForm):
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=128)])
    given_name = StringField('First Name', validators=[Length(max=64)])
    surname = StringField('Last Name', validators=[Length(max=64)])
    job_title = StringField('Job Title', validators=[Length(max=128)])
    department = StringField('Department', validators=[Length(max=128)])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, message='Password must be at least 8 characters'),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password')
    ])

    def validate_new_password(self, field):
        """Validate password strength"""
        password = field.data
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character')

