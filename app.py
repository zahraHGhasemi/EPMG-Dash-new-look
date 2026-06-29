
from flask import Flask, render_template, url_for
from flask_login import LoginManager
from auth.models import db, User, Study
from auth.auth_routes import auth_bp
from dash_app.app import init_dash
from auth.admin_routes import admin_bp
from flask_session import Session
from flask import redirect, request
from data_provider.sql_data import SQLDataProvider
from utils.dashboard_settings import get_dashboard_settings
from utils.schema_migrations import ensure_scenario_study_fk_schema, ensure_series_color_schema
import os
import tempfile
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv



load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL")
# print("Environment DB_URL:", os.getenv("DB_URL"))
# print("Database URL:", app.config["SQLALCHEMY_DATABASE_URI"])
db.init_app(app)

with app.app_context():
    db.create_all()
    ensure_scenario_study_fk_schema()
    # ensure_series_color_schema()

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)


session_file_dir = Path(
    os.getenv(
        "SESSION_FILE_DIR",
        Path(tempfile.gettempdir()) / "epmg_dashboard_flask_session",
    )
)
session_file_dir.mkdir(parents=True, exist_ok=True)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = str(session_file_dir)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

Session(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_studies():
    provider = SQLDataProvider(session=db.session)

    return {
        "recent_studies": provider.get_recent_studies(),
        "archive_studies": provider.get_archive_studies(),
        "ongoing_studies": provider.get_ongoing_studies()
    }
@app.route("/")
def home():
    return redirect(url_for("dash_home"))
@app.route("/dashboard", strict_slashes=False)
def dash_home():
    study_id = request.args.get("study_id")
    settings = get_dashboard_settings()
    default_tab = settings["default_tab"]
    tab = request.args.get("tab", default_tab)
    provider = SQLDataProvider(session=db.session)
    query_params = request.args.to_dict()
    if "tab" not in query_params or not query_params["tab"]:
        query_params["tab"] = tab

    if not study_id:
        chosen_study = None
        if settings.get("default_study_id"):
            chosen_study = db.session.get(Study, int(settings["default_study_id"]))

        if chosen_study:
            query_params["study_id"] = chosen_study.id
            return redirect(url_for("dash_home", **query_params))

        latest_study = provider.get_latest_recent_study()
        if latest_study:
            # redirect to /dash?study_id=<latest>
            query_params["study_id"] = latest_study.id
            return redirect(url_for("dash_home", **query_params))
        else:
            return "No recent study available", 404

    return render_template("home.html")

init_dash(app)

if __name__ == "__main__":
    app.run(debug=True) 
