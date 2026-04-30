

from urllib.parse import parse_qs
from dash import Input, Output

from auth.models import Study, StudyAbout
from components.about import ABOUT_MARKDOWN_ID


def register_about_callbacks(app):
    @app.callback(
        Output(ABOUT_MARKDOWN_ID, "children"),
        Input("url", "search")
    )
    def load_about_from_db(search):
        qs = parse_qs((search or "").lstrip("?"))
        study_id = qs.get("study_id", [None])[0]

        if not study_id:
            return "No study selected."

        about = StudyAbout.query.filter_by(study_id=int(study_id)).first()
        study = Study.query.get(int(study_id))
        study_name = study.name if study else f"Study {study_id}"

        about = StudyAbout.query.filter_by(study_id=int(study_id)).first()

        if not about:
            return f"## {study_name}\n\n_No About content has been added for this study yet._"

        return about.description