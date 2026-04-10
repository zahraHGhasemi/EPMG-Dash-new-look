from functools import wraps
from flask import Blueprint, Response, jsonify, render_template
from flask_login import login_required, current_user
from flask import request, redirect, flash, url_for
import pandas as pd
import os
import re
import io
import csv
from data_provider.sql_data import SQLDataProvider
from auth.models import (
    Table,
    Value,
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
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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


def _validate_color_conflicts(pending_updates: list[tuple[Series, str | None]]) -> None:
    updates_with_color = [(series, color) for series, color in pending_updates if color is not None]
    if not updates_with_color:
        return

    updating_ids = [series.id for series, _ in updates_with_color]
    affected_table_ids = sorted({series.table_id for series, _ in updates_with_color if series.table_id is not None})
    if not affected_table_ids:
        return

    query = select(Series.table_id, Series.id, Series.name, Series.color).where(
        Series.table_id.in_(affected_table_ids),
        Series.color.is_not(None),
    )
    if updating_ids:
        query = query.where(~Series.id.in_(updating_ids))

    existing_rows = db.session.execute(query).all()
    used_colors_by_table = {}
    for table_id, _, _, color in existing_rows:
        used_colors_by_table.setdefault(table_id, set()).add(color)

    for series, new_color in updates_with_color:
        used_colors = used_colors_by_table.setdefault(series.table_id, set())
        if new_color in used_colors:
            raise ValueError(
                f"Color '{new_color}' is already used in table '{series.table_id}'."
            )
        used_colors.add(new_color)


def _get_selected_table_context(provider, selected_category: str | None, selected_table_id: int | None) -> dict:
    categories = provider.get_categories()
    normalized_category = (selected_category or "").strip()
    if normalized_category not in categories:
        normalized_category = categories[0] if categories else None

    tables_query = Table.query
    if normalized_category:
        tables_query = tables_query.filter(Table.category == normalized_category)
    tables_for_category = tables_query.order_by(Table.title, Table.name).all()

    if not any(table.id == selected_table_id for table in tables_for_category):
        selected_table_id = tables_for_category[0].id if tables_for_category else None

    selected_table = db.session.get(Table, selected_table_id) if selected_table_id else None
    selected_series = []
    if selected_table:
        selected_series = (
            Series.query
            .filter(Series.table_id == selected_table.id)
            .order_by(Series.name)
            .all()
        )

    return {
        "categories": categories,
        "selected_category": normalized_category,
        "tables_for_category": tables_for_category,
        "selected_table": selected_table,
        "selected_series": selected_series,
    }


def _normalize_series_form_lists(series_ids, original_series_titles, series_color_updates, original_series_colors):
    if len(series_color_updates) < len(series_ids):
        series_color_updates += [None] * (len(series_ids) - len(series_color_updates))
    if len(original_series_titles) < len(series_ids):
        original_series_titles += [""] * (len(series_ids) - len(original_series_titles))
    if len(original_series_colors) < len(series_ids):
        original_series_colors += [None] * (len(series_ids) - len(original_series_colors))


def _collect_series_form_state(form) -> tuple[list[int], dict[int, dict[str, str | None]], dict[int, dict[str, str | None]]]:
    series_updates = form.getlist("series_title")
    series_ids = form.getlist("series_id")
    original_series_titles = form.getlist("original_series_title")
    series_color_updates = form.getlist("series_color")
    original_series_colors = form.getlist("original_series_color")
    _normalize_series_form_lists(
        series_ids,
        original_series_titles,
        series_color_updates,
        original_series_colors,
    )

    changed_series_ids = []
    changed_series_values = {}
    current_series_values = {}

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
        series_id = int(sid)
        current_series_values[series_id] = {
            "title": normalized_new_title,
            "color": validated_color,
        }

        if (
            normalized_new_title != normalized_original_title
            or validated_color != validated_original_color
        ):
            changed_series_ids.append(series_id)
            changed_series_values[series_id] = {
                "title": normalized_new_title,
                "color": validated_color,
            }

    return changed_series_ids, changed_series_values, current_series_values


def _apply_table_title_update(form, table: Table) -> None:
    new_table_title = (form.get("table_title") or "").strip()
    original_table_title = (form.get("original_table_title") or "").strip()
    if new_table_title != original_table_title:
        table.title = new_table_title or table.name


def _apply_series_values(series_rows: list[Series], values_by_name: dict[str, dict[str, str | None]]) -> None:
    pending_color_updates = [
        (series, values_by_name[series.name]["color"])
        for series in series_rows
    ]
    _validate_color_conflicts(pending_color_updates)

    for series in series_rows:
        new_values = values_by_name[series.name]
        series.title = new_values["title"] or series.name
        if new_values["color"] is not None:
            series.color = new_values["color"]


def _apply_series_updates_for_table_only(changed_series_ids, changed_series_values) -> list[Series]:
    if not changed_series_ids:
        return []

    changed_series = {
        series.id: series
        for series in Series.query.filter(Series.id.in_(changed_series_ids)).all()
    }
    affected_series = [
        changed_series[series_id]
        for series_id in changed_series_ids
        if series_id in changed_series
    ]
    if not affected_series:
        return []

    values_by_name = {
        series.name: changed_series_values[series.id]
        for series in affected_series
    }
    _apply_series_values(affected_series, values_by_name)
    return affected_series


def _apply_series_updates_globally(selected_table_id: int, current_series_values) -> list[Series]:
    selected_table_series = (
        Series.query
        .filter(Series.table_id == selected_table_id)
        .order_by(Series.name, Series.id)
        .all()
    )
    values_by_name = {
        series.name: current_series_values[series.id]
        for series in selected_table_series
        if series.id in current_series_values
    }
    if not values_by_name:
        return []

    affected_series = (
        Series.query
        .filter(Series.name.in_(list(values_by_name.keys())))
        .order_by(Series.table_id, Series.name)
        .all()
    )
    _apply_series_values(affected_series, values_by_name)
    return affected_series


def _save_edit_titles_form(form) -> tuple[str, str, str, int | None]:
    selected_category = (form.get("selected_category") or "").strip()
    selected_table_id = form.get("selected_table_id", type=int)
    propagate_series = (form.get("propagate_series") or "table_only").strip()

    if not selected_table_id:
        raise ValueError("Choose a table before saving.")

    table = db.session.get(Table, selected_table_id)
    if not table:
        raise ValueError("Selected table was not found.")

    if selected_category and table.category != selected_category:
        raise ValueError("Selected table does not belong to the chosen sector.")

    _apply_table_title_update(form, table)
    changed_series_ids, changed_series_values, current_series_values = _collect_series_form_state(form)

    if propagate_series == "global":
        affected_series = _apply_series_updates_globally(selected_table_id, current_series_values)
        message = f"Saved table updates and propagated series title/color changes to {len(affected_series)} rows."
    else:
        _apply_series_updates_for_table_only(changed_series_ids, changed_series_values)
        message = "Titles and colors updated successfully!"

    db.session.commit()
    return message, "success", selected_category, selected_table_id


def _handle_edit_titles_post(form) -> tuple[str, str, str, int | None]:
    selected_category = (form.get("selected_category") or "").strip()
    selected_table_id = form.get("selected_table_id", type=int)

    try:
        return _save_edit_titles_form(form)
    except IntegrityError:
        db.session.rollback()
        return (
            "Could not save edits because a color would be duplicated inside a table.",
            "danger",
            selected_category,
            selected_table_id,
        )
    except Exception as e:
        db.session.rollback()
        return (
            f"Could not save edits: {e}",
            "danger",
            selected_category,
            selected_table_id,
        )


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
        studies_ongoing = provider.get_ongoing_studies()
        studies_ongoing = [study.name for study in studies_ongoing]
        return render_template("admin/remove_study.html", studies_recent=studies_recent, studies_archive=studies_archive, studies_ongoing=studies_ongoing)

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
    provider = SQLDataProvider(db.session)
    if request.method == "POST":
        message, category, selected_category, selected_table_id = _handle_edit_titles_post(request.form)
        flash(message, category)
        return redirect(url_for("admin.edit_titles", category=selected_category, table_id=selected_table_id))

    context = _get_selected_table_context(
        provider,
        request.args.get("category"),
        request.args.get("table_id", type=int),
    )

    return render_template(
        "admin/edit_titles.html",
        category_dict=CATEGORY_DICT,
        **context,
    )


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


def get_scenario_download_data(scenario_id, download_format="melted", preview=False, preview_limit=10):
    scenario = db.session.get(Scenario, scenario_id)
    if not scenario:
        return None, None, "Scenario not found."

    rows = (
        db.session.query(
            Table.name.label("tableName"),
            Table.title.label("tableTitle"),
            Table.label.label("label"),
            Series.name.label("seriesName"),
            Series.title.label("seriesTitle"),
            Value.year.label("Year"),
            Value.value.label("Value"),
        )
        .join(Series, Value.series_id == Series.id)
        .join(Table, Series.table_id == Table.id)
        .filter(Value.scenario_id == scenario.id)
        .order_by(Table.name.asc(), Series.name.asc(), Value.year.asc())
        .all()
    )

    if not rows:
        return scenario, {"columns": [], "rows": []}, None

    if download_format == "wide":
        grouped = {}
        all_years = set()

        for row in rows:
            key = (
                scenario.name,
                row.tableName,
                row.tableTitle,
                row.label,
                row.seriesName,
                row.seriesTitle,
            )

            if key not in grouped:
                grouped[key] = {}

            grouped[key][row.Year] = row.Value
            all_years.add(row.Year)

        sorted_years = sorted(all_years)

        columns = [
            "scenario",
            "tableName",
            "tableTitle",
            "label",
            "seriesName",
            "seriesTitle",
            *[str(year) for year in sorted_years],
        ]

        data_rows = []
        for key, year_values in grouped.items():
            row_dict = {
                "scenario": key[0],
                "tableName": key[1],
                "tableTitle": key[2],
                "label": key[3],
                "seriesName": key[4],
                "seriesTitle": key[5],
            }

            for year in sorted_years:
                row_dict[str(year)] = year_values.get(year, "")

            data_rows.append(row_dict)

        if preview:
            data_rows = data_rows[:preview_limit]

        return scenario, {"columns": columns, "rows": data_rows}, None

    columns = [
        "scenario",
        "tableName",
        "tableTitle",
        "label",
        "seriesName",
        "seriesTitle",
        "Year",
        "Value",
    ]

    data_rows = [
        {
            "scenario": scenario.name,
            "tableName": row.tableName,
            "tableTitle": row.tableTitle,
            "label": row.label,
            "seriesName": row.seriesName,
            "seriesTitle": row.seriesTitle,
            "Year": row.Year,
            "Value": row.Value,
        }
        for row in rows
    ]

    if preview:
        data_rows = data_rows[:preview_limit]

    return scenario, {"columns": columns, "rows": data_rows}, None

@admin_bp.route("/preview_download_tables", methods=["POST"])
@login_required
@admin_required
def preview_download_tables():
    data = request.get_json(silent=True) or {}

    scenario_id = data.get("scenario_id")
    download_format = data.get("download_format", "melted")

    if not scenario_id:
        return jsonify({"error": "Scenario is required."}), 400

    scenario, result, error = get_scenario_download_data(
        scenario_id=scenario_id,
        download_format=download_format,
        preview=True,
        preview_limit=10,
    )

    if error:
        return jsonify({"error": error}), 404

    return jsonify(result)

@admin_bp.route("/download_tables", methods=["GET", "POST"])
@login_required
@admin_required
def download_tables():
    scenarios = Scenario.query.order_by(Scenario.name.asc()).all()

    if request.method == "GET":
        return render_template("admin/download_tables.html", scenarios=scenarios)

    scenario_id = request.form.get("scenario")
    download_format = request.form.get("download_format", "melted")

    if not scenario_id:
        flash("Please select a scenario.", "warning")
        return render_template("admin/download_tables.html", scenarios=scenarios)

    scenario, result, error = get_scenario_download_data(
        scenario_id=scenario_id,
        download_format=download_format,
        preview=False,
    )

    if error:
        flash(error, "danger")
        return render_template("admin/download_tables.html", scenarios=scenarios)

    if not result["rows"]:
        flash("No data was found for the selected scenario.", "warning")
        return render_template("admin/download_tables.html", scenarios=scenarios)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=result["columns"])
    writer.writeheader()
    writer.writerows(result["rows"])

    csv_data = output.getvalue()
    output.close()

    safe_scenario_name = (
        scenario.name.strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    filename = f"{safe_scenario_name}_{download_format}_tables.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )


@admin_bp.route("/edit_overview", methods=["GET", "POST"])
@login_required
@admin_required
def edit_overview():
    
    return render_template("admin/edit_overview.html")