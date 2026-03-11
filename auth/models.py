# from tokenize import String
# from unittest.mock import Base
from flask_login import UserMixin
# from database import Base
# from utils.database_utils import Base
import colorsys
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, select
from sqlalchemy.orm import Session as SASession



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
    color = db.Column(db.String(32))
    __table_args__ = (
        db.UniqueConstraint('table_id', 'name', name='uq_table_series'),
        db.UniqueConstraint('table_id', 'color', name='uq_series_table_color'),
    )


def pastel_continuous_palette(n: int, s: float = 0.35, v: float = 0.95) -> list[str]:
    if n <= 0:
        return []
    colors = []
    for i in range(n):
        h = i / n
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        colors.append(f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}")
    return colors


def normalize_series_color(color: str | None) -> str | None:
    if color is None:
        return None
    normalized = color.strip().lower()
    return normalized or None


def next_available_series_color(used_colors: set[str]) -> str:
    normalized_used = {normalize_series_color(c) for c in used_colors if normalize_series_color(c)}
    total = len(normalized_used) + 1
    while True:
        candidate = pastel_continuous_palette(total)[-1]
        if candidate not in normalized_used:
            return candidate
        total += 1


def used_series_colors_for_table(session, table_id: int) -> set[str]:
    rows = session.execute(
        select(Series.color).where(
            Series.table_id == table_id,
            Series.color.is_not(None),
        )
    ).scalars().all()
    return {c for c in rows if c}


@event.listens_for(SASession, "before_flush")
def assign_or_validate_series_colors_before_flush(session, flush_context, instances):
    pending_series = [obj for obj in session.new if isinstance(obj, Series)]
    if not pending_series:
        return

    used_by_table: dict[int, set[str]] = {}
    uncolored_by_table: dict[int, list[Series]] = {}

    for series in pending_series:
        if series.table_id is None:
            continue

        series.color = normalize_series_color(series.color)

        if series.table_id not in used_by_table:
            used_by_table[series.table_id] = used_series_colors_for_table(session, series.table_id)

        used_colors = used_by_table[series.table_id]
        if series.color is None:
            uncolored_by_table.setdefault(series.table_id, []).append(series)
            continue

        if series.color in used_colors:
            raise ValueError(
                f"Color '{series.color}' is already used for table_id={series.table_id}."
            )
        used_colors.add(series.color)

    for table_id, rows in uncolored_by_table.items():
        used_colors = used_by_table[table_id]
        if not used_colors:
            # First-time assignment for this table: generate one palette for all new series.
            palette = pastel_continuous_palette(len(rows))
            for series, color in zip(rows, palette):
                series.color = color
                used_colors.add(color)
            continue

        # Future additions: continue assigning with the same pastel palette approach.
        for series in rows:
            color = next_available_series_color(used_colors)
            series.color = color
            used_colors.add(color)


@event.listens_for(Series, "before_update")
def normalize_series_color_before_update(mapper, connection, target):
    target.color = normalize_series_color(target.color)

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
