# from flask import Blueprint, render_template, request, redirect, url_for, flash
# from flask_login import login_user, logout_user, login_required, current_user
# from werkzeug.security import check_password_hash
# from auth.models import User
# from database import SessionLocal

# from auth.models import User
# from database import SessionLocal

# auth_bp = Blueprint("auth", __name__)

# @auth_bp.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]

#         db = SessionLocal()
#         user = db.query(User).filter(User.username == username).first()
#         db.close()

#         if user and check_password_hash(user.password_hash, password):
#             login_user(user)
#             return redirect("/")  # redirect to main Dash page
        
#         flash("Invalid username or password")

#     return render_template("login.html")

# @auth_bp.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     return redirect("/")

from flask import Blueprint, render_template, request, redirect, current_app
from flask_login import login_user, logout_user, login_required
from database import SessionLocal
from auth.models import User
from werkzeug.security import check_password_hash
from flask import session
import os

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = SessionLocal()
        user = db.query(User).filter_by(
            username=request.form["username"].strip()
        ).first()

        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            return redirect("/")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
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
