import re

from auth.models import Table, Value, db, Series, normalize_series_color
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError


HEX_COLOR_RE = re.compile(r"^#[0-9a-f]{6}$")


def _validate_series_color(value: str | None) -> str | None:
    """Normalize a submitted series color and require a #RRGGBB hex value."""
    normalized = normalize_series_color(value)
    if normalized is None:
        return None
    if not HEX_COLOR_RE.fullmatch(normalized):
        raise ValueError(f"Invalid color '{value}'. Use #RRGGBB.")
    return normalized


def _validate_color_conflicts(pending_updates: list[tuple[Series, str | None]]) -> None:
    """Reject color updates that would duplicate a color within the same table."""
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


def get_selected_table_context(provider, selected_category: str | None, selected_table_id: int | None) -> dict:
    """Build category, table, and series state for admin pages with table pickers."""
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
    """Pad form lists so each submitted series has title and color values to compare."""
    if len(series_color_updates) < len(series_ids):
        series_color_updates += [None] * (len(series_ids) - len(series_color_updates))
    if len(original_series_titles) < len(series_ids):
        original_series_titles += [""] * (len(series_ids) - len(original_series_titles))
    if len(original_series_colors) < len(series_ids):
        original_series_colors += [None] * (len(series_ids) - len(original_series_colors))


def _collect_series_form_state(form) -> tuple[list[int], dict[int, dict[str, str | None]], dict[int, dict[str, str | None]]]:
    """Read series title/color fields and separate changed values from current values."""
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
    """Update a table title from the edit form, falling back to the internal table name."""
    new_table_title = (form.get("table_title") or "").strip()
    original_table_title = (form.get("original_table_title") or "").strip()
    if new_table_title != original_table_title:
        table.title = new_table_title or table.name


def _apply_series_values(series_rows: list[Series], values_by_name: dict[str, dict[str, str | None]]) -> None:
    """Apply validated title/color values to matching series rows."""
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
    """Apply changed series title/color values only to the selected table's rows."""
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
    """Propagate selected-table series title/color values to series with the same names."""
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


def save_edit_titles_form(form) -> tuple[str, str, str, int | None]:
    """Validate and save table title plus series title/color changes from the edit form."""
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


def handle_edit_titles_post(form) -> tuple[str, str, str, int | None]:
    """Wrap edit-title saving with rollback and user-facing flash message details."""
    selected_category = (form.get("selected_category") or "").strip()
    selected_table_id = form.get("selected_table_id", type=int)

    try:
        return save_edit_titles_form(form)
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


def delete_table_and_related_rows(selected_category: str, selected_table_id: int | None) -> tuple[str, str, str, int | None]:
    """Delete a table and its related series/value rows after validating selection."""
    if not selected_table_id:
        raise ValueError("Choose a table before deleting.")

    table = db.session.get(Table, selected_table_id)
    if not table:
        raise ValueError("Selected table was not found.")

    if selected_category and table.category != selected_category:
        raise ValueError("Selected table does not belong to the chosen sector.")

    table_title = table.title or table.name

    series_ids_subquery = select(Series.id).where(Series.table_id == table.id)
    db.session.execute(
        delete(Value).where(Value.series_id.in_(series_ids_subquery))
    )
    db.session.execute(delete(Series).where(Series.table_id == table.id))
    db.session.delete(table)
    db.session.commit()

    return (
        f'Table "{table_title}" deleted successfully.',
        "success",
        selected_category,
        None,
    )
