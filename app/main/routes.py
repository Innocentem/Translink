from flask import render_template, Blueprint
from flask_login import login_required, current_user

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("home.html", title="Welcome to Translink")

@main.route("/about")
def about():
    return render_template("about.html", title="About Translink")

@main.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title="Dashboard", user=current_user)
