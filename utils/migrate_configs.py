import json
from pathlib import Path
from sqlalchemy import select


def migrate_configs_to_db(db_session, flash_fn=None):
    """Migrate existing JSON config files into the `app_config` DB table when missing.

    Args:
        db_session: SQLAlchemy session (e.g., `db.session`).
        flash_fn: optional function like `flask.flash` to report user-visible messages.
    Raises:
        Exception on unexpected errors.
    """
    from auth.models import AppConfig
    from utils.dashboard_settings import SETTINGS_PATH
    from utils.update_db_table import load_table_upload_rules

    try:
        # dashboard_settings
        has_dashboard = db_session.execute(
            select(AppConfig.key).where(AppConfig.key == "dashboard_settings")
        ).scalar_one_or_none()
        if has_dashboard is None and SETTINGS_PATH.exists():
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                text = f.read()
            db_session.add(AppConfig(key="dashboard_settings", json_value=text))

        # table_info
        has_table_info = db_session.execute(
            select(AppConfig.key).where(AppConfig.key == "table_info")
        ).scalar_one_or_none()
        rules = load_table_upload_rules() or {}
        if has_table_info is None and rules:
            db_session.add(AppConfig(key="table_info", json_value=json.dumps(rules, indent=2) + "\n"))

        db_session.commit()
        if flash_fn:
            flash_fn("Configuration migration completed.", "success")
    except Exception as exc:
        # Rollback to avoid leaving session in bad state
        try:
            db_session.rollback()
        except Exception:
            pass
        message = f"Configuration migration failed: {exc}"
        if flash_fn:
            flash_fn(message, "danger")
        # Re-raise so callers can also handle/log
        raise
