from functools import wraps
from flask import Blueprint, app, render_template, abort
from flask_login import login_required, current_user
from flask import request, redirect, flash, url_for, Blueprint, render_template
import pandas as pd
from data_provider.sql_data import SQLDataProvider
from auth.models import Table, db, Scenario, StudyScenario, Study, Series, StudyAbout
from utils.update_db_table import process_uploaded_csv

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return "Forbidden", 403
        return func(*args, **kwargs)
    return wrapper

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

    files = request.files.getlist("files")
    scenario_name = request.form.get("scenario_name")

    if not files or not scenario_name:
        flash("Scenario name and files are required", "danger")
        return redirect(url_for("admin.upload_scenario"))
    
    try:
        for file in files:
            df = pd.read_csv(file.stream)

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
        # process the submitted form
        table_updates = request.form.getlist("table_title")
        table_ids = request.form.getlist("table_id")
        for tid, new_title in zip(table_ids, table_updates):
            table = Table.query.get(int(tid))
            if table:
                table.title = new_title.strip() or table.name  # fallback to name if empty
        db.session.commit()

        series_updates = request.form.getlist("series_title")
        series_ids = request.form.getlist("series_id")
        for sid, new_title in zip(series_ids, series_updates):
            series = Series.query.get(int(sid))
            if series:
                series.title = new_title.strip() or series.name
        db.session.commit()

        flash("Titles updated successfully!", "success")
        return redirect("/admin/edit_titles")

    # GET: show all tables and series
    tables = Table.query.order_by(Table.name).all()
    series = Series.query.order_by(Series.name).all()
    return render_template("admin/edit_titles.html", tables=tables, series=series)


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
