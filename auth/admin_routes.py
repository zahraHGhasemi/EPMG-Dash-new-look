from functools import wraps
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from utils.data_loader import load_and_concat_uploaded_files
from utils.dataframe_melter import melt_dataframe
from utils.database_utils import write_scenario_to_database, execute_sql
from flask import request, redirect, flash, url_for

from data_provider.sql_data import SQLDataProvider


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

    df_all = load_and_concat_uploaded_files(files)
    df_prepared, _ = melt_dataframe(df_all)

    # df_prepared["Scenario"] = scenario_name

    result = write_scenario_to_database(df_prepared)

    if result["written"]:
        flash(
            f"Added scenarios: {', '.join(result['written'])}",
            "success"
        )

    if result["skipped"]:
        flash(
            f"Skipped existing scenarios: {', '.join(result['skipped'])}",
            "warning"
        )
    return redirect(url_for("admin.upload_scenario"))


@admin_bp.route("/remove_scenario", methods=["GET"])
@login_required
@admin_required
def remove_scenarios_page():
    provider = SQLDataProvider()
    scenarios = provider.get_scenarios()  
    return render_template("remove_scenario.html", scenarios=scenarios)

@admin_bp.route("/delete-scenarios", methods=["POST"])
@login_required
@admin_required
def delete_scenarios():
    scenarios = request.form.getlist("scenarios")  

    if not scenarios:
        flash("No scenarios selected", "warning")
        return redirect(url_for("admin.remove_scenarios_page"))

    # Delete each scenario from the database
    deleted_scenarios = []
    for scenario in scenarios:
        try:
            execute_sql(
                'DELETE FROM observations WHERE "Scenario" = :scenario',
                params={"scenario": scenario}
            )
            deleted_scenarios.append(scenario)
        except Exception as e:
            flash(f"Error deleting {scenario}: {str(e)}", "danger")

    if deleted_scenarios:
        flash(f"Deleted scenarios: {', '.join(deleted_scenarios)}", "success")

    return redirect(url_for("admin.remove_scenarios_page"))




from flask import current_app
import os
import json

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@admin_bp.route("/dictionaries", methods=["GET", "POST"])
@login_required
@admin_required
def config_dictionary():
    # paths to JSON config files
    table_file = os.path.join(current_app.root_path, "config", "chartsTitles.json")
    series_file = os.path.join(current_app.root_path, "config", "seriesTitles.json")

    table_dict = load_json(table_file)
    series_dict = load_json(series_file)

    if request.method == "POST":
        dict_type = request.form.get("dict_type")  # "table" or "series"
        key = request.form.get("key")
        value = request.form.get("value")

        if not dict_type or not key or not value:
            flash("All fields are required", "danger")
            return redirect(url_for("admin.config_dictionary"))

        # update the selected dictionary
        if dict_type == "table":
            table_dict[key] = value
            save_json(table_file, table_dict)
        elif dict_type == "series":
            series_dict[key] = value
            save_json(series_file, series_dict)

        flash(f"{dict_type.capitalize()} dictionary updated successfully!", "success")
        return redirect(url_for("admin.config_dictionary"))

    return render_template(
        "admin/dictionaries.html",
        table_dict=table_dict,
        series_dict=series_dict
    )