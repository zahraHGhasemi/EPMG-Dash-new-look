import re


def _slugify_filename_part(value):
    text = str(value or "").strip()
    if not text:
        return "unknown"

    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "_", text)
    text = text.strip("_")
    return text or "unknown"


def build_download_filename(tab_name, scenario, metric_or_table_name, year_start, year_end, suffix=None):
    parts = [
        _slugify_filename_part(tab_name),
        _slugify_filename_part(scenario),
        _slugify_filename_part(metric_or_table_name),
        f"{year_start}_{year_end}",
    ]

    if suffix:
        parts.append(_slugify_filename_part(suffix))

    return "_".join(parts)


def build_plotly_download_config(tab_name, scenario, metric_or_table_name, year_start, year_end, suffix=None):
    return {
        "responsive": True,
        "toImageButtonOptions": {
            "format": "png",
            "filename": build_download_filename(
                tab_name,
                scenario,
                metric_or_table_name,
                year_start,
                year_end,
                suffix=suffix,
            ),
        },
    }
