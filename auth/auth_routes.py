from flask import Blueprint, flash, render_template, request, redirect, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session
import os

from auth.models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Render the login page and authenticate submitted username/password credentials."""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = (
            db.session
            .query(User)
            .filter_by(username=username)
            .first()
        )

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect("/")

        # optional: flash message later
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password", "warning")  
            return redirect("/login")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Log out the current user and remove any temporary uploaded scenario file."""
    # Remove user-uploaded temporary scenario (if exists)
    scenario = session.pop("user_scenario", None)

    if scenario:
        path = os.path.join(
            current_app.instance_path,
            "user_uploads",
            f"{scenario['id']}.parquet"
        )
        if os.path.exists(path):
            os.remove(path)

    session.clear()
    logout_user()
    return redirect("/")

