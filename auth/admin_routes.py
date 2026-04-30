from functools import wraps
from flask import Blueprint, Response, jsonify, render_template
from flask_login import login_required, current_user
from flask import request, redirect, flash, url_for
import os
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
)
from utils.edit_titles import (
    delete_table_and_related_rows,
    get_selected_table_context,
    handle_edit_titles_post,
)
from utils.update_db_table import (
    SUPPORTED_UPLOAD_FORMAT,
    TABLE_UPLOAD_FORMAT,
    add_table_upload_rule,
    get_source_table_options,
    get_table_upload_source_map,
    get_table_upload_options,
    load_and_validate_uploaded_csvs,
    process_uploaded_csv_by_table_names,
    process_uploaded_csv,
    validate_table_upload_selections,
    validate_upload_format,
)
from utils.dashboard_settings import (
    get_dashboard_settings,
    get_overview_metrics,
    save_dashboard_settings,
    save_overview_metrics,
)
from config.constants import CATEGORY_DICT

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


def admin_required(func):
    """Decorator that allows only authenticated users with the admin role."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Block non-admin requests before calling the protected view."""
        if not current_user.is_authenticated or current_user.role != "admin":
            return "Forbidden", 403
        return func(*args, **kwargs)
    return wrapper


def _infer_scenario_name_from_files(files):
    """Use the first uploaded filename stem as a fallback scenario name."""
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
    """Render the main admin panel landing page."""
    return render_template("admin/panel.html")


@admin_bp.route("/table-upload-rules", methods=["GET", "POST"])
@login_required
@admin_required
def manage_table_upload_rules():
    """Display and create table upload rules used by the table-based CSV uploader."""
    if request.method == "POST":
        try:
            new_table_name = add_table_upload_rule(
                table_name=request.form.get("new_table_name"),
                source_name=request.form.get("new_table_source_name"),
                keep_dimensions=request.form.get("new_table_keep_dimensions"),
                default_unit=request.form.get("new_table_default_unit"),
                aggregation=request.form.get("new_table_aggregation"),
                filter_column=request.form.get("new_table_filter_column"),
                filter_values_text=request.form.get("new_table_filter_values"),
                reverse_sign=bool(request.form.get("new_table_reverse_sign")),
                cumulate=bool(request.form.get("new_table_cumulate")),
            )
            flash(
                f"table_info updated successfully. New table '{new_table_name}' is now available.",
                "success",
            )
        except Exception as e:
            flash(f"Could not add new table definition: {e}", "danger")
        return redirect(url_for("admin.manage_table_upload_rules"))

    return render_template(
        "admin/table_upload_rules.html",
        available_source_table_options=get_source_table_options(),
    )

    
@admin_bp.route("/upload", methods=["GET", "POST"])
@login_required
@admin_required
def upload_scenario():
    """Upload scenario CSV data in either supported single-file or table-based format."""
    def _render_upload_page(selected_format=SUPPORTED_UPLOAD_FORMAT):
        """Render the upload form with the requested upload format selected."""
        if selected_format not in {SUPPORTED_UPLOAD_FORMAT, TABLE_UPLOAD_FORMAT}:
            selected_format = SUPPORTED_UPLOAD_FORMAT
        return render_template(
            "upload.html",
            title="Upload scenario to main database",
            selected_upload_format=selected_format,
            available_table_upload_options=get_table_upload_options(),
            table_upload_source_map=get_table_upload_source_map(),
        )

    if request.method == "GET":
        requested_format = (request.args.get("upload_format") or SUPPORTED_UPLOAD_FORMAT).strip()
        return _render_upload_page(requested_format)

    files = [f for f in request.files.getlist("files") if (getattr(f, "filename", "") or "").strip()]
    scenario_name = (request.form.get("scenario_name") or "").strip()
    upload_format = request.form.get("upload_format")
    selected_table_names = request.form.getlist("table_upload_names")
    overwrite_existing_tables = bool(request.form.get("overwrite_existing_tables"))

    if not scenario_name:
        scenario_name = _infer_scenario_name_from_files(files)

    if not files:
        flash("At least one CSV file is required", "danger")
        return redirect(url_for("admin.upload_scenario", upload_format=upload_format or SUPPORTED_UPLOAD_FORMAT))

    if upload_format == SUPPORTED_UPLOAD_FORMAT and len(files) > 1:
        flash("Format 1 accepts only one CSV file. Please upload a single file.", "danger")
        return redirect(url_for("admin.upload_scenario", upload_format=SUPPORTED_UPLOAD_FORMAT))

    if upload_format == SUPPORTED_UPLOAD_FORMAT and not scenario_name:
        flash("Scenario name is required", "danger")
        return redirect(url_for("admin.upload_scenario", upload_format=SUPPORTED_UPLOAD_FORMAT))
    
    try:
        selected_upload_format = validate_upload_format(upload_format)

        # For the scenario-based format, the scenario name is determined by the filename and not required as a separate input, so we only validate the scenario name for the single-file format.
        if selected_upload_format == SUPPORTED_UPLOAD_FORMAT:
            df = load_and_validate_uploaded_csvs(files)

            # Check if scenario exists
            exists = db.session.query(Scenario).filter_by(name=scenario_name).first()
            if exists:
                flash(
                    f"Scenario '{scenario_name}' already exists. "
                    "Please delete it first before uploading a new one.",
                    "warning"
                )
                return redirect(url_for("admin.upload_scenario", upload_format=SUPPORTED_UPLOAD_FORMAT))

            process_uploaded_csv(
                df=df,  
                scenario_name=scenario_name,
                engine=db.get_engine()
            )

            flash(f"Scenario '{scenario_name}' uploaded successfully!", "success")
        # For the table-based format, we validate the selected table names and process each uploaded CSV according to its corresponding table definition.
        else:
            selected_table_names = validate_table_upload_selections(selected_table_names)
            uploaded_scenarios = process_uploaded_csv_by_table_names(
                table_names=selected_table_names,
                files=files,
                engine=db.get_engine(),
                overwrite_existing_tables=overwrite_existing_tables,
            )
            flash(
                f"Selected tables uploaded successfully for scenario(s): "
                f"{', '.join(uploaded_scenarios)}.",
                "success",
            )

    except Exception as e:
        flash(f"Upload failed: {e}", "danger")

    return redirect(url_for("admin.upload_scenario", upload_format=selected_upload_format if 'selected_upload_format' in locals() else upload_format or SUPPORTED_UPLOAD_FORMAT))


@admin_bp.route("/default_values", methods=["GET", "POST"])
@login_required
@admin_required
def default_values():
    """View and save dashboard-wide defaults such as years, study, scenario, and sector."""
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
            payload["overview_metrics"] = get_dashboard_settings().get("overview_metrics", [])

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
    """List scenarios and delete the selected scenarios from the database."""
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
    """List studies by status and delete the selected studies from the database."""
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
    """List studies and add a new study with its status."""
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
    """Manage which scenarios are linked to each study."""
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
    """Render and process the admin page for editing table and series display labels."""
    provider = SQLDataProvider(db.session)
    if request.method == "POST":
        message, category, selected_category, selected_table_id = handle_edit_titles_post(request.form)
        flash(message, category)
        return redirect(url_for("admin.edit_titles", category=selected_category, table_id=selected_table_id))

    context = get_selected_table_context(
        provider,
        request.args.get("category"),
        request.args.get("table_id", type=int),
    )

    return render_template(
        "admin/edit_titles.html",
        category_dict=CATEGORY_DICT,
        **context,
    )


@admin_bp.route("/edit_titles/delete_table", methods=["POST"])
@login_required
@admin_required
def delete_table_from_edit_titles():
    """Handle table deletion from the edit-titles page and redirect back to context."""
    selected_category = (request.form.get("selected_category") or "").strip()
    selected_table_id = request.form.get("selected_table_id", type=int)

    try:
        message, category, redirect_category, redirect_table_id = delete_table_and_related_rows(
            selected_category,
            selected_table_id,
        )
        flash(message, category)
    except Exception as e:
        db.session.rollback()
        flash(f"Could not delete table: {e}", "danger")
        redirect_category = selected_category
        redirect_table_id = selected_table_id

    redirect_kwargs = {}
    if redirect_category:
        redirect_kwargs["category"] = redirect_category
    if redirect_table_id:
        redirect_kwargs["table_id"] = redirect_table_id
    return redirect(url_for("admin.edit_titles", **redirect_kwargs))


@admin_bp.route("/study_about", methods=["GET", "POST"])
@login_required
@admin_required
def study_about():    
    """Create or update markdown-style About text for a selected study."""
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
    """Build melted or wide scenario table data for previews and CSV downloads."""
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
    """Return a JSON preview of downloadable scenario table data."""
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
    """Render the download page or stream selected scenario table data as a CSV file."""
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
def _build_overview_metric(table: Table, category: str, form) -> dict:
    """Validate overview metric form input and return the saved metric structure."""
    metric_title = (form.get("metric_title") or "").strip()
    divide_by_raw = (form.get("divide_by") or "").strip()
    chosen_series = [
        series_title.strip()
        for series_title in form.getlist("series_titles")
        if (series_title or "").strip()
    ]

    if not metric_title:
        raise ValueError("Please enter the overview metric name.")
    if not chosen_series:
        raise ValueError("Please select at least one series.")
    if not divide_by_raw:
        raise ValueError("Please enter a divide by value.")

    try:
        divide_by = float(divide_by_raw)
    except ValueError as exc:
        raise ValueError("Divide by value must be a valid number.") from exc

    if divide_by == 0:
        raise ValueError("Divide by value cannot be zero.")

    valid_series_titles = {
        (series.title or series.name).strip()
        for series in Series.query.filter_by(table_id=table.id).all()
    }
    invalid_series = [series_title for series_title in chosen_series if series_title not in valid_series_titles]
    if invalid_series:
        raise ValueError("Some selected series do not belong to the selected table.")

    existing_titles = {metric["title"].casefold() for metric in get_overview_metrics()}
    if metric_title.casefold() in existing_titles:
        raise ValueError("An overview metric with that name already exists.")

    return {
        "title": metric_title,
        "category": category,
        "table_id": table.id,
        "table_title": table.title or table.name,
        "series_titles": chosen_series,
        "divide_by": divide_by,
    }



@admin_bp.route("/edit_overview", methods=["GET", "POST"])
@login_required
@admin_required
def edit_overview():
    """Render and process overview metric creation for selected tables and series."""
    provider = SQLDataProvider(db.session)
    selected_category = (request.form.get("selected_category") or request.args.get("category") or "").strip()
    selected_table_id = request.form.get("selected_table_id", type=int) or request.args.get("table_id", type=int)
    metric_title_value = (request.form.get("metric_title") or "").strip()
    divide_by_value = (request.form.get("divide_by") or "").strip()
    selected_series_titles = {
        series_title.strip()
        for series_title in request.form.getlist("series_titles")
        if (series_title or "").strip()
    }

    if request.method == "POST":
        if not selected_table_id:
            flash("Choose a table before saving an overview metric.", "warning")
        else:
            try:
                selected_table = db.session.get(Table, selected_table_id)
                if not selected_table:
                    raise ValueError("Selected table was not found.")
                if selected_category and selected_table.category != selected_category:
                    raise ValueError("Selected table does not belong to the chosen sector.")

                overview_metrics = get_overview_metrics()
                overview_metrics.append(_build_overview_metric(selected_table, selected_category, request.form))
                save_overview_metrics(overview_metrics)

                flash(f'Overview metric "{metric_title_value}" added successfully.', "success")
                return redirect(url_for("admin.edit_overview", category=selected_category, table_id=selected_table_id))
            except ValueError as exc:
                flash(str(exc), "danger")

    context = get_selected_table_context(provider, selected_category, selected_table_id)

    return render_template(
        "admin/edit_overview.html",
        overview_metrics=get_overview_metrics(),
        category_dict=CATEGORY_DICT,
        metric_title_value=metric_title_value,
        divide_by_value=divide_by_value,
        selected_series_titles=selected_series_titles,
        **context,
    )


@admin_bp.route("/edit_overview/delete/<int:metric_index>", methods=["POST"])
@login_required
@admin_required
def delete_overview_metric(metric_index: int):
    """Delete an overview metric from dashboard settings by its list position."""
    overview_metrics = get_overview_metrics()
    if metric_index < 0 or metric_index >= len(overview_metrics):
        flash("Overview metric was not found.", "danger")
        return redirect(url_for("admin.edit_overview"))

    deleted_metric = overview_metrics.pop(metric_index)
    save_overview_metrics(overview_metrics)
    flash(f'Overview metric "{deleted_metric["title"]}" deleted.', "success")
    return redirect(url_for("admin.edit_overview"))
