from flask import Blueprint, render_template, request, redirect, flash, session, current_app
from flask_login import login_required, current_user
import pandas as pd
import uuid
from utils.data_loader import load_and_concat_uploaded_files
from utils.dataframe_melter import melt_dataframe
user_bp = Blueprint("user", __name__, url_prefix="/user")
import os

@user_bp.route("/panel")
@login_required
def user_panel():
    if current_user.role != "user":
        # optional safety redirect
        return render_template("403.html"), 403

    return render_template("/user/panel.html", user=current_user)




@user_bp.route("/upload", methods=["GET", "POST"])
@login_required

def upload_scenario():
    if current_user.role != "user":
        return "Forbidden", 403
    
    UPLOAD_ROOT = os.path.join(current_app.instance_path, "user_uploads")
    os.makedirs(UPLOAD_ROOT, exist_ok=True)
    
    if request.method == "POST":
        files = request.files.getlist("files")
        scenario_name = request.form.get("scenario_name")

        if not files or not scenario_name:
            flash("Scenario name and files are required", "danger")
            return redirect("/user/upload")

        # 🔹 Remove previous upload (one scenario per user)
        old = session.get("user_scenario")
        if old:
            old_path = os.path.join(UPLOAD_ROOT, f"{old['id']}.parquet")
            if os.path.exists(old_path):
                os.remove(old_path)

        # 🔹 Load + prepare
        df_raw = load_and_concat_uploaded_files(files)
        df_prepared, scenarios = melt_dataframe(df_raw)

        # 🔹 Save as Parquet
        scenario_id = str(uuid.uuid4())
        save_path = os.path.join(UPLOAD_ROOT, f"{scenario_id}.parquet")

        df_prepared.to_parquet(
            save_path,
            engine="pyarrow",
            index=False
        )

        # 🔹 Store metadata in session
        session["user_scenario"] = {
            "id": scenario_id,
            "name": scenario_name
        }

        flash("Scenario uploaded successfully", "success")
        return redirect("/user/dashboard")

    # return render_template("user/upload.html")
    return render_template("upload.html")




@user_bp.route("/dashboard")
@login_required
def user_dashboard_page():
    return render_template("user/dashboard.html")