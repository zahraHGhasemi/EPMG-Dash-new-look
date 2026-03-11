

# # import pandas as pd
# # import numpy as np

# # import dash
# # from dash import dcc, html, Input, Output

# # import plotly.express as px
# # import dash_bootstrap_components as dbc
# # from callbacks.overview_callback import register_overview_callbacks

# # from callbacks.tab_content_callbacks import register_tab_content_callbacks
# # from callbacks.upload_file_callback import register_upload_callback
# # from utils.dataframe_melter import get_scenarios, get_data_melted
# # from callbacks.all_chart_callback import register_all_chart_callbacks
# # from callbacks.compare_callback import register_compare_chart_callbacks
# # from callbacks.sankey_callback import register_sankey_callback

# # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
# #     suppress_callback_exceptions=True)
# # server = app.server


# # scenarios = get_scenarios()
# # # all_data_melted = get_data_melted()
# # app.title = "Energy Scenarios Dashboard"

# # app.layout = html.Div([
# #     html.Div([
# #         html.Img(
# #             src="/assets/EPMG LOGO.png",
# #             style={
# #                 "height": "60px",
# #                 "margin-right": "15px"
# #             }
# #         ),
# #         html.H1(
# #             "Energy Policy & Modeling Group Dashboard",
# #             style={
# #                 "margin": "0",
# #                 "font-size": "36px"
# #             }
# #         )
# #     ],
# #     style={
# #         "display": "flex",
# #         "alignItems": "center",     # vertical alignment
# #         "justifyContent": "center", # horizontal centering
# #         "padding": "20px"
# #     }), 
    
# #     dbc.Row([       
# #         dbc.Col([
# #             dcc.Tabs(id ='tabs', value = 'about', children =[
# #                 dcc.Tab(label = 'About', value = 'about'),
# #                 dcc.Tab(label='Overview', value='overview'),
# #                 # dcc.Tab(label='Chart Detail', value='all-charts'),
# #                 dcc.Tab(label='Charts', value='compare-scenarios'),
# #                 dcc.Tab(label= "Sankey Diagram", value = 'sankey')
# #             ]),
# #     html.Div(id='tab-content', children='Loading...'),
# #         ], width=12)
# #     ])
    
# # ])

# # register_tab_content_callbacks(app)

# # register_overview_callbacks(app) 
# # register_upload_callback(app)

# # register_all_chart_callbacks(app)
# # register_compare_chart_callbacks(app)
# # register_sankey_callback(app)

# # import os
# # if __name__ == '__main__':
# #     port = int(os.environ.get("PORT", 8050))
# #     app.run(host="0.0.0.0", port=port, debug=True)
# #     # app.run(debug=True)

# from flask import Flask
# from dash_app.app import init_dash
# from flask_login import LoginManager
# from auth.models import User
# from database import SessionLocal
# from auth.routes import auth_bp

# import os
# # --- Flask app ---
# server = Flask(__name__)
# server.secret_key = os.getenv("SECRET_KEY", "dev-secret")

# server.register_blueprint(auth_bp)

# # --- Flask-Login setup ---
# login_manager = LoginManager()
# login_manager.init_app(server)
# login_manager.login_view = "auth.login"  # route to redirect if login required

# @login_manager.user_loader
# def load_user(user_id):
#     db = SessionLocal()
#     return db.query(User).get(int(user_id))


# # --- Dash app ---
# app = init_dash(server)
# from database import SessionLocal
# from sqlalchemy import text


# if __name__ == "__main__":
    
#     app.run(debug=True)


from flask import Flask, render_template, url_for
from flask_login import LoginManager
from auth.models import db, User, Study
# from utils.database_utils import SessionLocal
from auth.auth_routes import auth_bp
from dash_app.app import init_dash
from auth.admin_routes import admin_bp
from auth.user_routes import user_bp
from flask_session import Session
from dash_app.user_dash import init_user_dash
from flask import redirect, request
from data_provider.sql_data import SQLDataProvider
from utils.dashboard_settings import get_dashboard_settings
from utils.schema_migrations import ensure_series_color_schema
import os
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
    # ensure_series_color_schema()

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)


app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

Session(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
# @login_manager.user_loader
# def load_user(user_id):
#     db = SessionLocal()
#     return db.query(User).get(int(user_id))

@app.context_processor
def inject_studies():
    provider = SQLDataProvider(session=db.session)

    return {
        "recent_studies": provider.get_recent_studies(),
        "archive_studies": provider.get_archive_studies(),
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
init_user_dash(app)

if __name__ == "__main__":
    app.run(debug=True) 
