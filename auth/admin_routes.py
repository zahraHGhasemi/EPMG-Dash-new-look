from functools import wraps
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask import request, redirect, flash, url_for
import pandas as pd
import os
import re
from data_provider.sql_data import SQLDataProvider
from auth.models import (
    Table,
    db,
    Scenario,
    StudyScenario,
    Study,
    Series,
    StudyAbout,
    normalize_series_color,
)
from utils.update_db_table import process_uploaded_csv
from utils.dashboard_settings import get_dashboard_settings, save_dashboard_settings
from config.constants import CATEGORY_DICT

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

HEX_COLOR_RE = re.compile(r"^#[0-9a-f]{6}$")


def _validate_series_color(value: str | None) -> str | None:
    normalized = normalize_series_color(value)
    if normalized is None:
        return None
    if not HEX_COLOR_RE.fullmatch(normalized):
        raise ValueError(f"Invalid color '{value}'. Use #RRGGBB.")
    return normalized


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return "Forbidden", 403
        return func(*args, **kwargs)
    return wrapper


def _infer_scenario_name_from_files(files):
    for file in files:
        filename = (getattr(file, "filename", "") or "").strip()
        if not filename:
            continue
        stem = os.path.splitext(os.path.basename(filename))[0].strip()
        if stem:
            return stem
    return ""

@admin_bp.route("/panel")
@login_required
@admin_required
def admin_panel():
    return render_template("admin/panel.html")

    
@admin_bp.route("/upload", methods=["GET", "POST"])
@login_required
@admin_required
def upload_scenario():

    if request.method == "GET":
        return render_template(
            "upload.html",
            title="Upload scenario to main database"
        )

    files = [f for f in request.files.getlist("files") if (getattr(f, "filename", "") or "").strip()]
    scenario_name = (request.form.get("scenario_name") or "").strip()
    if not scenario_name:
        scenario_name = _infer_scenario_name_from_files(files)

    if not files:
        flash("At least one CSV file is required", "danger")
        return redirect(url_for("admin.upload_scenario"))

    if not scenario_name:
        flash("Scenario name is required", "danger")
        return redirect(url_for("admin.upload_scenario"))
    
    try:
        dataframes = [pd.read_csv(file.stream) for file in files]
        df = pd.concat(dataframes, ignore_index=True)

        # Check if scenario exists
        exists = db.session.query(Scenario).filter_by(name=scenario_name).first()
        if exists:
            flash(
                f"Scenario '{scenario_name}' already exists. "
                "Please delete it first before uploading a new one.",
                "warning"
            )
            return redirect(url_for("admin.upload_scenario"))

        process_uploaded_csv(
            df=df,  
            scenario_name=scenario_name,
            engine=db.get_engine()
        )

        flash(f"Scenario '{scenario_name}' uploaded successfully!", "success")

    except Exception as e:
        flash(f"Upload failed: {e}", "danger")

    return redirect(url_for("admin.upload_scenario"))


@admin_bp.route("/default_values", methods=["GET", "POST"])
@login_required
@admin_required
def default_values():
    provider = SQLDataProvider(db.session)
    studies = Study.query.order_by(Study.name.asc()).all()
    categories = provider.get_categories()
    study_scenarios_map = {
        str(study.id): [s.name for s in provider.get_scenarios_for_study(study.id)]
        for study in studies
    }
    sector_subsectors_map = {
        str(category): provider.get_subcategories(category)
        for category in categories
    }

    if request.method == "POST":
        try:
            payload = {
                "start_year": request.form.get("start_year"),
                "end_year": request.form.get("end_year"),
                "default_start_year": request.form.get("default_start_year"),
                "default_end_year": request.form.get("default_end_year"),
                "default_tab": request.form.get("default_tab"),
                "overview_metric": request.form.get("overview_metric"),
                "overview_chart_type": request.form.get("overview_chart_type"),
                "sankey_mode": request.form.get("sankey_mode"),
                "default_study_id": request.form.get("default_study_id"),
                "default_scenario": request.form.get("default_scenario"),
                "default_sector": request.form.get("default_sector"),
                "default_subsector": request.form.get("default_subsector"),
            }

            selected_study = (payload["default_study_id"] or "").strip()
            selected_scenario = (payload["default_scenario"] or "").strip()
            selected_sector = (payload["default_sector"] or "").strip()
            selected_subsector = (payload["default_subsector"] or "").strip()

            if selected_scenario and not selected_study:
                raise ValueError("Choose a default study before choosing a default scenario.")

            if selected_study:
                allowed_scenarios = set(study_scenarios_map.get(selected_study, []))
                if selected_scenario and selected_scenario not in allowed_scenarios:
                    raise ValueError("Default scenario must belong to the selected default study.")

            if selected_subsector and not selected_sector:
                raise ValueError("Choose a default sector before choosing a default subsector.")

            if selected_sector:
                allowed_subsectors = set(sector_subsectors_map.get(selected_sector, []))
                if selected_subsector and selected_subsector not in allowed_subsectors:
                    raise ValueError("Default subsector must belong to the selected default sector.")

            updated = save_dashboard_settings(payload)
            flash("Dashboard defaults saved.", "success")
            return render_template(
                "admin/default_values.html",
                settings=updated,
                studies=studies,
                categories=categories,
                category_dict=CATEGORY_DICT,
                study_scenarios_map=study_scenarios_map,
                sector_subsectors_map=sector_subsectors_map,
            )
        except Exception as e:
            flash(f"Could not save defaults: {e}", "danger")

    settings = get_dashboard_settings()
    return render_template(
        "admin/default_values.html",
        settings=settings,
        studies=studies,
        categories=categories,
        category_dict=CATEGORY_DICT,
        study_scenarios_map=study_scenarios_map,
        sector_subsectors_map=sector_subsectors_map,
    )



@admin_bp.route("/remove_scenario", methods=["GET", "POST"])
@login_required
@admin_required
def remove_scenarios_page():
    if request.method == "GET":
        provider = SQLDataProvider(db.session())
        scenarios = provider.get_scenarios()  
        return render_template("admin/remove_scenario.html", scenarios=scenarios)


    if request.method == "POST":
        scenarios = request.form.getlist("scenarios")  

        if not scenarios:
            flash("No scenarios selected", "warning")
            return redirect(url_for("admin.remove_scenarios_page"))

        # Delete each scenario from the database
        deleted_scenarios = []
        for scenario in scenarios:
            try:
                scenario_obj = (
                    db.session.query(Scenario)
                    .filter_by(name=scenario)
                    .first()
                )
                if scenario_obj:
                    db.session.delete(scenario_obj)
                    db.session.commit()

                
                deleted_scenarios.append(scenario)
            except Exception as e:
                flash(f"Error deleting {scenario}: {str(e)}", "danger")

        if deleted_scenarios:
            flash(f"Deleted scenarios: {', '.join(deleted_scenarios)}", "success")

        return redirect(url_for("admin.remove_scenarios_page"))
    
    return redirect(url_for("admin.remove_scenarios_page"))



@admin_bp.route("/remove_study", methods=["GET", "POST"])
@login_required
@admin_required
def remove_studies_page():
    if request.method == "GET":
        provider = SQLDataProvider(db.session())
        studies_recent = provider.get_recent_studies()
        studies_recent = [study.name for study in studies_recent]
        studies_archive = provider.get_archive_studies()
        studies_archive = [study.name for study in studies_archive]
        return render_template("admin/remove_study.html", studies_recent=studies_recent, studies_archive=studies_archive)

    if request.method == "POST":
        studies = request.form.getlist("studies")  

        if not studies:
            flash("No studies selected", "warning")
            return redirect(url_for("admin.remove_studies_page"))

        # Delete each study from the database
        deleted_studies = []
        for study in studies:
            try:
                study_obj = (
                    db.session.query(Study)
                    .filter_by(name=study)
                    .first()
                )
                if study_obj:
                    db.session.delete(study_obj)
                    db.session.commit()

                
                deleted_studies.append(study)
            except Exception as e:
                flash(f"Error deleting {study}: {str(e)}", "danger")

        if deleted_studies:
            flash(f"Deleted studies: {', '.join(deleted_studies)}", "success")

        return redirect(url_for("admin.remove_studies_page"))
    
    return redirect(url_for("admin.remove_studies_page"))



@admin_bp.route("/studies", methods=["GET", "POST"])
@login_required
@admin_required
def admin_studies():
    if request.method == "POST":
        name = request.form.get("name")
        status = request.form.get("status")
        
        if not name or not status:
            flash("Please enter both name and status")
            return redirect(url_for("admin.admin_studies"))
        
        new_study = Study(name=name, status=status)
        db.session.add(new_study)
        db.session.commit()
        
        flash("Study added successfully!")
        return redirect(url_for("admin.admin_studies"))
    
    # GET request → list existing studies
    studies = Study.query.order_by(Study.id.desc()).all()
    return render_template("admin/add_study.html", studies=studies)

@admin_bp.route("/study-scenarios", methods=["GET", "POST"])
@login_required
@admin_required
def study_scenarios_page():
    studies = Study.query.order_by(Study.name).all()
    scenarios = Scenario.query.order_by(Scenario.name).all()

    if request.method == "POST":
        study_id = int(request.form.get("study_id"))
        selected_scenario_ids = request.form.getlist("scenarios")  # list of scenario ids as str

        StudyScenario.query.filter_by(study_id=study_id).delete()

        for scenario_id in selected_scenario_ids:
            db.session.add(StudyScenario(
                study_id=study_id,
                scenario_id=int(scenario_id)
            ))

        db.session.commit()
        flash("Study-Scenario links updated successfully.", "success")
        return redirect(url_for("admin.study_scenarios_page"))

    return render_template(
        "admin/study_scenarios.html",
        studies=studies,
        scenarios=scenarios
    )

@admin_bp.route("/edit_titles", methods=["GET", "POST"])
@login_required
@admin_required
def edit_titles():
    if request.method == "POST":
        try:
            table_updates = request.form.getlist("table_title")
            table_ids = request.form.getlist("table_id")
            original_table_titles = request.form.getlist("original_table_title")
            changed_table_ids = []
            changed_table_titles = {}

            for tid, new_title, original_title in zip(table_ids, table_updates, original_table_titles):
                normalized_new_title = (new_title or "").strip()
                normalized_original_title = (original_title or "").strip()
                if normalized_new_title != normalized_original_title:
                    table_id = int(tid)
                    changed_table_ids.append(table_id)
                    changed_table_titles[table_id] = normalized_new_title

            if changed_table_ids:
                changed_tables = {
                    table.id: table
                    for table in Table.query.filter(Table.id.in_(changed_table_ids)).all()
                }
                for table_id in changed_table_ids:
                    table = changed_tables.get(table_id)
                    if table:
                        table.title = changed_table_titles[table_id] or table.name

            series_updates = request.form.getlist("series_title")
            series_ids = request.form.getlist("series_id")
            original_series_titles = request.form.getlist("original_series_title")
            series_color_updates = request.form.getlist("series_color")
            original_series_colors = request.form.getlist("original_series_color")
            if len(series_color_updates) < len(series_ids):
                series_color_updates += [None] * (len(series_ids) - len(series_color_updates))
            if len(original_series_titles) < len(series_ids):
                original_series_titles += [""] * (len(series_ids) - len(original_series_titles))
            if len(original_series_colors) < len(series_ids):
                original_series_colors += [None] * (len(series_ids) - len(original_series_colors))

            changed_series_ids = []
            changed_series_values = {}

            for sid, new_title, original_title, new_color, original_color in zip(
                series_ids,
                series_updates,
                original_series_titles,
                series_color_updates,
                original_series_colors,
            ):
                normalized_new_title = (new_title or "").strip()
                normalized_original_title = (original_title or "").strip()
                validated_color = _validate_series_color(new_color)
                validated_original_color = _validate_series_color(original_color)

                if (
                    normalized_new_title != normalized_original_title
                    or validated_color != validated_original_color
                ):
                    series_id = int(sid)
                    changed_series_ids.append(series_id)
                    changed_series_values[series_id] = {
                        "title": normalized_new_title,
                        "color": validated_color,
                    }

            if changed_series_ids:
                changed_series = {
                    series.id: series
                    for series in Series.query.filter(Series.id.in_(changed_series_ids)).all()
                }
                for series_id in changed_series_ids:
                    series = changed_series.get(series_id)
                    if series:
                        series.title = changed_series_values[series_id]["title"] or series.name
                        if changed_series_values[series_id]["color"] is not None:
                            series.color = changed_series_values[series_id]["color"]

            db.session.commit()
            flash("Titles and colors updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Could not save edits: {e}", "danger")
        return redirect("/admin/edit_titles")

    # GET: show tables with their related series grouped together
    tables = Table.query.order_by(Table.name).all()
    all_series = (
        Series.query
        .order_by(Series.table_id, Series.name)
        .all()
    )

    series_by_table_id = {}
    for item in all_series:
        series_by_table_id.setdefault(item.table_id, []).append(item)

    grouped_titles = [
        {
            "table": table,
            "series": series_by_table_id.get(table.id, []),
        }
        for table in tables
    ]

    return render_template("admin/edit_titles.html", grouped_titles=grouped_titles)


@admin_bp.route("/study_about", methods=["GET", "POST"])
@login_required
@admin_required
def study_about():    
    studies = Study.query.order_by(Study.name.asc()).all()

    selected_study_id = request.args.get("study_id", type=int)

    if request.method == "POST":
        selected_study_id = request.form.get("study_id", type=int)
        about_md = (request.form.get("about_md") or "").strip()

        if not selected_study_id:
            flash("Please choose a study.", "danger")
            return redirect(url_for("admin.study_about"))

        if not about_md:
            flash("About content cannot be empty.", "danger")
            return redirect(url_for("admin.study_about", study_id=selected_study_id))

        study = Study.query.get(selected_study_id)
        if not study:
            flash("Study not found.", "danger")
            return redirect(url_for("admin.study_about"))

        # UPSERT: update if exists, else create
        about = StudyAbout.query.filter_by(study_id=selected_study_id).first()
        if about:
            about.description = about_md
        else:
            db.session.add(StudyAbout(study_id=selected_study_id, description=about_md))

        db.session.commit()
        flash(f"Saved About for “{study.name}”.", "success")
        return redirect(url_for("admin.study_about", study_id=selected_study_id))

    # GET: prefill about_md if present
    about_text = ""
    study_name = None
    if selected_study_id:
        study = Study.query.get(selected_study_id)
        study_name = study.name if study else None
        about = StudyAbout.query.filter_by(study_id=selected_study_id).first()
        about_text = about.description if about else ""

    return render_template(
        "admin/study_about.html",
        studies=studies,
        selected_study_id=selected_study_id,
        selected_study_name=study_name,
        about_text=about_text,
    )



