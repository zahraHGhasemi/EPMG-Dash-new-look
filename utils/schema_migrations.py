from sqlalchemy import inspect, text

from auth.models import db, next_available_series_color, normalize_series_color, pastel_continuous_palette


def ensure_scenario_study_fk_schema() -> None:
    """Ensure scenarios.study_id preserves scenarios when a study is deleted."""
    engine = db.engine
    inspector = inspect(engine)

    if "scenarios" not in inspector.get_table_names() or "studies" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("scenarios")}
    if "study_id" not in existing_columns:
        return

    foreign_keys = [
        fk
        for fk in inspector.get_foreign_keys("scenarios")
        if fk.get("constrained_columns") == ["study_id"]
        and fk.get("referred_table") == "studies"
    ]
    expected_name = "fk_scenarios_study_id_studies"
    already_set_null = any(
        (fk.get("options") or {}).get("ondelete", "").upper() == "SET NULL"
        for fk in foreign_keys
    )

    if already_set_null:
        return

    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as conn:
        invalid = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM scenarios
                LEFT JOIN studies ON studies.id = scenarios.study_id
                WHERE scenarios.study_id IS NOT NULL
                AND studies.id IS NULL
                """
            )
        ).scalar()
        if invalid:
            raise RuntimeError(
                "Cannot add scenarios.study_id foreign key because some scenarios "
                "reference studies that no longer exist."
            )

        for fk in foreign_keys:
            name = fk.get("name")
            if name:
                conn.execute(text(f'ALTER TABLE scenarios DROP CONSTRAINT "{name}"'))

        conn.execute(
            text(
                f"""
                ALTER TABLE scenarios
                ADD CONSTRAINT {expected_name}
                FOREIGN KEY (study_id)
                REFERENCES studies(id)
                ON DELETE SET NULL
                """
            )
        )


def ensure_series_color_schema() -> None:
    """Add series.color and uniqueness per table for existing databases."""
    engine = db.engine
    inspector = inspect(engine)

    if "series" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("series")}
    has_unique_table_color = _has_unique_table_color(inspector)

    with engine.begin() as conn:
        if "color" not in existing_columns:
            conn.execute(text("ALTER TABLE series ADD COLUMN color VARCHAR(32)"))

        if not has_unique_table_color:
            duplicate = conn.execute(
                text(
                    """
                    SELECT table_id, color, COUNT(*) AS cnt
                    FROM series
                    WHERE color IS NOT NULL
                    GROUP BY table_id, color
                    HAVING COUNT(*) > 1
                    LIMIT 1
                    """
                )
            ).first()
            if duplicate:
                raise RuntimeError(
                    "Cannot enforce unique color per table in 'series' because "
                    f"duplicates exist for table_id={duplicate.table_id}, color={duplicate.color}."
                )

            conn.execute(
                text(
                    "CREATE UNIQUE INDEX uq_series_table_color "
                    "ON series (table_id, color)"
                )
            )

    backfill_missing_series_colors()


def backfill_missing_series_colors() -> None:
    """Assign colors only to series rows that do not already have one."""
    engine = db.engine
    inspector = inspect(engine)

    if "series" not in inspector.get_table_names():
        return

    with engine.begin() as conn:
        table_ids = conn.execute(
            text(
                """
                SELECT DISTINCT table_id
                FROM series
                WHERE table_id IS NOT NULL
                ORDER BY table_id
                """
            )
        ).scalars().all()

        for table_id in table_ids:
            rows = conn.execute(
                text(
                    """
                    SELECT id, color
                    FROM series
                    WHERE table_id = :table_id
                    ORDER BY name, id
                    """
                ),
                {"table_id": table_id},
            ).all()
            if not rows:
                continue

            existing_colors = [
                normalize_series_color(row.color)
                for row in rows
                if normalize_series_color(row.color)
            ]
            missing_rows = [row for row in rows if not normalize_series_color(row.color)]
            if not missing_rows:
                continue

            if not existing_colors:
                palette = pastel_continuous_palette(len(missing_rows))
                assigned_colors = palette
            else:
                used_colors = set(existing_colors)
                assigned_colors = []
                for _ in missing_rows:
                    color = next_available_series_color(used_colors)
                    used_colors.add(color)
                    assigned_colors.append(color)

            for row, color in zip(missing_rows, assigned_colors):
                conn.execute(
                    text("UPDATE series SET color = :color WHERE id = :series_id"),
                    {"color": color, "series_id": row.id},
                )


def _has_unique_table_color(inspector) -> bool:
    for constraint in inspector.get_unique_constraints("series"):
        if set(constraint.get("column_names") or []) == {"table_id", "color"}:
            return True

    for index in inspector.get_indexes("series"):
        if index.get("unique") and set(index.get("column_names") or []) == {"table_id", "color"}:
            return True

    return False
