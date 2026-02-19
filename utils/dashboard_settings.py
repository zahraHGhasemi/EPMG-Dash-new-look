import json
from pathlib import Path

from config.constants import (
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    DEFAULT_TAB,
    END_YEAR,
    START_YEAR,
)


SETTINGS_PATH = Path(__file__).resolve().parent.parent / "config" / "dashboard_settings.json"

DEFAULT_SETTINGS = {
    "start_year": START_YEAR,
    "end_year": END_YEAR,
    "default_start_year": DEFAULT_START_YEAR,
    "default_end_year": DEFAULT_END_YEAR,
    "default_tab": DEFAULT_TAB,
    "overview_metric": "FEC",
    "overview_chart_type": "pie",
    "sankey_mode": 1,
    "default_study_id": None,
    "default_scenario": None,
    "default_sector": None,
    "default_subsector": None,
}


def _sanitize(settings):
    data = dict(DEFAULT_SETTINGS)
    data.update(settings or {})

    data["start_year"] = int(data["start_year"])
    data["end_year"] = int(data["end_year"])
    data["default_start_year"] = int(data["default_start_year"])
    data["default_end_year"] = int(data["default_end_year"])
    data["sankey_mode"] = int(data["sankey_mode"])
    data["default_tab"] = str(data["default_tab"])
    data["overview_metric"] = str(data["overview_metric"])
    data["overview_chart_type"] = str(data["overview_chart_type"])

    data["default_study_id"] = (
        int(data["default_study_id"])
        if data.get("default_study_id") not in (None, "", "None")
        else None
    )
    data["default_scenario"] = (
        str(data["default_scenario"]).strip()
        if data.get("default_scenario") not in (None, "", "None")
        else None
    )
    data["default_sector"] = (
        str(data["default_sector"]).strip()
        if data.get("default_sector") not in (None, "", "None")
        else None
    )
    data["default_subsector"] = (
        str(data["default_subsector"]).strip()
        if data.get("default_subsector") not in (None, "", "None")
        else None
    )

    if data["start_year"] > data["end_year"]:
        raise ValueError("Start year must be less than or equal to end year.")

    if not (data["start_year"] <= data["default_start_year"] <= data["end_year"]):
        raise ValueError("Default start year must be inside the selected year range.")

    if not (data["start_year"] <= data["default_end_year"] <= data["end_year"]):
        raise ValueError("Default end year must be inside the selected year range.")

    if data["default_start_year"] > data["default_end_year"]:
        raise ValueError("Default start year must be less than or equal to default end year.")

    if data["default_tab"] not in {"about", "overview", "charts", "sankey"}:
        raise ValueError("Default tab must be one of: about, overview, charts, sankey.")

    if data["overview_metric"] not in {"FEC", "Import", "Renewable"}:
        raise ValueError("Overview metric must be one of: FEC, Import, Renewable.")

    if data["overview_chart_type"] not in {"bar", "pie"}:
        raise ValueError("Overview chart type must be one of: bar, pie.")

    if data["sankey_mode"] not in {0, 1}:
        raise ValueError("Sankey mode must be 0 or 1.")

    return data


def get_dashboard_settings():
    if not SETTINGS_PATH.exists():
        return dict(DEFAULT_SETTINGS)

    with SETTINGS_PATH.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    return _sanitize(loaded)


def save_dashboard_settings(settings):
    cleaned = _sanitize(settings)
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)
    return cleaned
