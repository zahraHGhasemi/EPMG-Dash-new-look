# from tokenize import String
# from unittest.mock import Base
from flask_login import UserMixin
# from database import Base
# from utils.database_utils import Base
from flask_sqlalchemy import SQLAlchemy



db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")


class Study(db.Model):
    __tablename__ = "studies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    scenarios = db.relationship(
        "Scenario",
        secondary="study_scenarios",
        back_populates="studies"
    )
    
    about = db.relationship(
        "StudyAbout",
        back_populates="study",
        uselist=False,
        cascade="all, delete-orphan"
    )
class Scenario(db.Model):
    __tablename__ = "scenarios"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    studies = db.relationship(
        "Study",
        secondary="study_scenarios",
        back_populates="scenarios"
    )

class StudyScenario(db.Model):
    __tablename__ = 'study_scenarios'
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'))
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id', ondelete='CASCADE'))
    __table_args__ = (
        db.UniqueConstraint('study_id', 'scenario_id', name='uq_study_scenario'),
    )

class Table(db.Model):
    __tablename__ = 'tables'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String)
    label = db.Column(db.String)    # e.g. TWh, MtCO2
    category = db.Column(db.String)

class Series(db.Model):
    __tablename__ = 'series'
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id', ondelete='CASCADE'))
    name = db.Column(db.String, nullable=False)
    title = db.Column(db.String)
    __table_args__ = (
        db.UniqueConstraint('table_id', 'name', name='uq_table_series'),
    )

class Year(db.Model):
    __tablename__ = 'years'
    year = db.Column(db.Integer, primary_key=True)

class Value(db.Model):
    __tablename__ = 'values'
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id', ondelete='CASCADE'))
    series_id = db.Column(db.Integer, db.ForeignKey('series.id', ondelete='CASCADE'))
    year = db.Column(db.Integer, db.ForeignKey('years.year'))
    value = db.Column(db.Float)

    __table_args__ = (
        db.UniqueConstraint('scenario_id', 'series_id', 'year', name='uq_value'),
    )

class StudyAbout(db.Model):
    __tablename__ = "study_about"

    id = db.Column(db.Integer, primary_key=True)

    study_id = db.Column(
        db.Integer,
        db.ForeignKey("studies.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    description = db.Column(db.Text, nullable=False)


    study = db.relationship(
        "Study",
        back_populates="about"
    )