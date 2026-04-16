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
    "overview_metric": "",
    "overview_chart_type": "pie",
    "sankey_mode": 1,
    "default_study_id": None,
    "default_scenario": None,
    "default_sector": None,
    "default_subsector": None,
    "overview_metrics": [],
}


def _normalize_overview_metric(metric):
    if isinstance(metric, dict):
        title = str(metric.get("title") or "").strip()
        category = str(metric.get("category") or "").strip()
        table_title = str(metric.get("table_title") or "").strip()
        table_id = metric.get("table_id")
        series_titles = [
            str(series_title).strip()
            for series_title in (metric.get("series_titles") or [])
            if str(series_title).strip()
        ]
        divide_by = metric.get("divide_by")
    # elif isinstance(metric, (list, tuple)) and len(metric) >= 4:
    #     title = str(metric[0] or "").strip()
    #     category = ""
    #     table_title = str(metric[2] or "").strip()
    #     table_id = None
    #     series_titles = [
    #         str(series_title).strip()
    #         for series_title in (metric[1] or [])
    #         if str(series_title).strip()
    #     ]
    #     divide_by = metric[3]
    else:
        return None

    if not title or not table_title or not series_titles:
        return None

    try:
        normalized_divide_by = float(divide_by)
    except (TypeError, ValueError):
        return None

    return {
        "title": title,
        "category": category,
        "table_title": table_title,
        "table_id": int(table_id) if table_id not in (None, "") else None,
        "series_titles": series_titles,
        "divide_by": normalized_divide_by,
    }


def get_overview_metrics(settings=None):
    if settings is None:
        if SETTINGS_PATH.exists():
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                settings = json.load(f)
        else:
            settings = {}

    source = dict(DEFAULT_SETTINGS)
    source.update(settings or {})
    metrics = source.get("overview_metrics") or []
    normalized_metrics = []
    for metric in metrics:
        normalized_metric = _normalize_overview_metric(metric)
        if normalized_metric:
            normalized_metrics.append(normalized_metric)
    return normalized_metrics


def save_overview_metrics(metrics):
    current_settings = get_dashboard_settings()
    updated_settings = dict(current_settings)
    updated_settings["overview_metrics"] = metrics
    return save_dashboard_settings(updated_settings)


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
    data["overview_metrics"] = get_overview_metrics(data)

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

    available_overview_metric_titles = {metric["title"] for metric in data["overview_metrics"]}
    if available_overview_metric_titles and data["overview_metric"] not in available_overview_metric_titles:
        data["overview_metric"] = next(iter(available_overview_metric_titles))

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
    current_settings = get_dashboard_settings()
    merged_settings = dict(current_settings)
    merged_settings.update(settings or {})
    if "overview_metrics" not in (settings or {}):
        merged_settings["overview_metrics"] = current_settings.get("overview_metrics", [])
    cleaned = _sanitize(merged_settings)
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)
    return cleaned
