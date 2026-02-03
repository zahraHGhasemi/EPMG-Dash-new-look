# from flask import Flask
# from auth.models import db   # import db
# import os

# app = Flask(__name__)

# app.config["SQLALCHEMY_DATABASE_URI"] =  'postgresql://neondb_owner:npg_L0YpAVZD4hKT@ep-sparkling-wind-abutfff5-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# db.init_app(app)

# with app.app_context():
#     db.create_all()
#     print("✅ Database tables created")
