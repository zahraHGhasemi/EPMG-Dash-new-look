# TIM Energy Scenarios Output Dashboard

This repository contains the Energy Policy & Modeling Group dashboard for TIM energy scenario outputs. It is a Flask web application that embeds a Dash dashboard for interactive scenario exploration and provides authenticated admin tools for maintaining studies, scenarios, display labels, dashboard defaults, and uploaded model data.

## Current Website Features

- Public dashboard entrypoint at `/dashboard`, with the Dash app mounted at `/dash/`
- Study-aware dashboard navigation for recent, ongoing, and archived studies
- Automatic redirect to the configured default study, or the latest recent study when no study is selected
- Dashboard tabs for About, Overview, Charts, and Sankey Diagram views
- Study-specific About content managed from the admin area
- Configurable overview metrics, chart type, default tab, year range, default scenario, sector, and subsector
- Scenario comparison charts by study, sector, table, year range, and series
- Sankey analysis driven by dashboard settings
- Authenticated admin panel for data, content, and configuration maintenance

## Admin Tools

Admin routes are registered under `/admin` and require a logged-in user with the `admin` role.

- `/admin/panel`: Admin landing page
- `/admin/upload`: Upload scenario CSV data to the main database
- `/admin/table-upload-rules`: Create, inspect, download, and delete table upload rules in `config/table_info.json`
- `/admin/download_tables`: Preview and download scenario table data as CSV in melted or wide format
- `/admin/studies`: Add studies, edit study names, assign study status, and create initial About text
- `/admin/study-scenarios`: Assign scenarios to studies and prevent duplicate scenario names within a study
- `/admin/study_about`: Edit the About text shown on the dashboard for a selected study
- `/admin/default_values`: Configure dashboard defaults, overview behavior, Sankey mode, and category labels
- `/admin/edit_titles`: Edit table and series display titles and series colors, or delete tables
- `/admin/edit_overview`: Add or delete configurable overview metrics
- `/admin/remove_scenario`: Delete scenarios
- `/admin/remove_study`: Delete studies

## Data Upload Formats

The website currently supports two admin upload workflows:

1. `table-series-year`
   - A single CSV format with `tableName`, `seriesName`, `label`, and one or more 4-digit year columns.
   - The admin chooses a target study and scenario name.
   - Existing scenarios can be overwritten either completely or only for the uploaded tables.

2. `table-raw-by-table`
   - A table-rule based upload format configured through `config/table_info.json`.
   - Admins choose one or more supported output tables and upload the required source CSV files.
   - Source files are validated against their table rules and transformed into dashboard-ready table, series, year, and value records.
   - Existing selected tables can be overwritten for matching scenarios.

## Project Structure

- `app.py`: Main Flask entrypoint, database setup, blueprint registration, study redirect logic, and Dash initialization
- `dash_app/`: Dash application setup, assets, tab layout, and callback registration
- `auth/`: Flask authentication routes, admin routes, SQLAlchemy models, and role checks
- `callbacks/`: Dash callbacks for About, Overview, Charts, Sankey, and tab state behavior
- `components/`: Reusable Dash layouts and chart components
- `config/`: Dashboard JSON configuration, table upload rules, chart titles, series titles, and constants
- `data_provider/`: SQL-backed data access helpers for studies, scenarios, categories, tables, series, and chart values
- `templates/`: Jinja templates for the embedded dashboard shell, login page, base layout, upload page, and admin pages
- `utils/`: Upload processing, schema migrations, plotting, settings persistence, title editing, category labels, and Sankey helpers
- `instance/`: Runtime instance files, including temporary user upload parquet files
- `init_db.py`: Database initialization helper
- `requirements.txt`: Python dependencies
- `Procfile` and `runtime.txt`: Deployment metadata for a Gunicorn-hosted Flask app

Generated or local-only folders such as `venv/`, `__pycache__/`, `flask_session/`, and `tmp_pycompile/` do not need to be committed or documented in detail.

## Database Model

The application stores dashboard data in SQLAlchemy models:

- `User`: Authenticated application users with a role field
- `Study`: Study groups with `recent`, `ongoing`, or `archive` status
- `Scenario`: Scenario names assigned to studies, unique per study
- `StudyAbout`: Markdown-style About text for each study
- `Table`: Dashboard table definitions, including category, title, and unit label
- `Series`: Series definitions for each table, including display title and color
- `Year`: Allowed year values
- `Value`: Numeric scenario values by scenario, series, and year

On startup, the app creates missing tables and runs lightweight schema checks such as the scenario-to-study foreign key migration.

## Configuration

Important configuration files:

- `config/dashboard_settings.json`: Default years, selected tab, default study/scenario/sector, overview settings, Sankey mode, and overview metrics
- `config/table_info.json`: Table upload rules used by the `table-raw-by-table` workflow
- `config/constants.py`: Category labels and shared constants
- `config/chartsTitles.json`, `config/chartsInfo.json`, and `config/seriesTitles.json`: Display metadata used by chart components

Most dashboard defaults can be edited from `/admin/default_values`; table upload rules can be edited from `/admin/table-upload-rules`.

## Local Setup

1. Create and activate a virtual environment.

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DB_URL=your-database-connection-string
```

4. Start the application:

```powershell
python app.py
```

The Flask app starts the Dash dashboard inside the same server. Visit `/dashboard` to use the website.

## Deployment

The repository includes a `Procfile` for running the app with Gunicorn:

```text
web: gunicorn app:app
```

Make sure the deployment environment provides `SECRET_KEY` and `DB_URL`, and that the target database is reachable by SQLAlchemy.

## Development Notes

- Uploaded user scenario files are stored under `instance/user_uploads/`.
- Flask server-side sessions are stored in `flask_session/` during local development.
- Use the admin pages where possible for dashboard settings, upload rules, and display metadata so JSON configuration and database state stay aligned.
- `pytest.ini` is configured to discover tests from a `tests/` folder when tests are present.
