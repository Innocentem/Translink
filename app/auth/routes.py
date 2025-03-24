from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm

auth = Blueprint('auth', __name__)

# Route for login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            # Return a JSON response indicating success
            return jsonify({'success': True, 'redirect_url': url_for('main.home')})
        else:
            # Return an error message if login fails
            return jsonify({'success': False, 'message': 'Invalid email or password.'})

    return render_template('login.html', title='Login', form=form)

# Route for logout
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))  # Redirect to home page after logging out

# Route for registration
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Email already registered.'})

        user = User(username=form.username.data,
                    email=form.email.data,
                    role='customer')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        # Respond with success and redirect URL
        return jsonify({'success': True, 'redirect_url': url_for('main.home')})

    return render_template('register.html', title='Register', form=form)
