# TIM Energy Scenarios Output Dashboard

This project is a Flask and Dash application for TIM outputs. It combines:

- Flask for routing, authentication, and admin pages
- Dash for interactive charts and dashboard views
- SQLAlchemy for database access and application models
- JSON first time configuration files for chart labels, table metadata, and dashboard defaults

The app appears to support multiple studies and scenarios, with separate admin tools for maintaining dashboard content and settings.

## Main Features


- Interactive dashboard pages for overview, chart comparison, and Sankey analysis
- Authentication and role-based access flows
- Admin pages for editing about study, editing titles, overview content, default values, dictionaries, and study/scenario data
- Config-driven chart and table labels
- Automated tests for selected admin functionality

## Project Structure

This is a high-level guide to the main folders:

- `auth/`: Flask blueprints, authentication routes, admin routes, user routes, and database models
- `callbacks/`: Dash callback registration and interaction logic for each dashboard section
- `components/`: Reusable Dash layout components for tabs, charts, navigation, and content blocks
- `config/`: JSON and Python configuration files such as chart titles, table info, constants, and dashboard settings
- `dash_app/`: Dash app initialization, assets, and dashboard bootstrapping
- `data_provider/`: Data access layer used to load studies, scenarios, and dashboard data
- `templates/`: Jinja templates for Flask pages, including admin and user pages
- `tests/`: Pytest test suite
- `utils/`: Shared helper functions for loading data, plotting charts, filtering data, schema updates, and dashboard settings
- `data/` and `data_new/`: Project data folders
- `instance/`: Runtime instance files such as uploaded parquet files

Generated or local-only folders you usually do not need to document in depth:

- `venv/`
- `__pycache__/`
- `flask_session/`
- `tmp_pycompile/`

## Important Entry Files

- `app.py`: Main Flask application entrypoint and Dash integration
- `database.py`: Database session configuration used by parts of the project
- `init_db.py`: Database initialization helper
- `requirements.txt`: Python dependencies
- `pytest.ini`: Test configuration

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the required environment variables:

```env
SECRET_KEY=your-secret-key
DB_URL=your-database-connection-string
```

4. Start the application:

```powershell
python app.py
```

The app runs through Flask and initializes the Dash dashboard inside the same server.

## Testing

Run the test suite with:

```powershell
pytest
```

## Documentation Plan

To improve documentation step by step, a good order is:

1. Main project `README.md`
2. Folder-level summaries
3. Function docstrings for core modules
4. Cleanup of commented-out code and unused imports
5. Test/documentation updates where behavior is unclear
