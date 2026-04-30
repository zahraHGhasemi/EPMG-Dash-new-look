import html

from dash import dcc, html
ABOUT_MARKDOWN_ID = "about-markdown"

def about_layout():
    """Generate the layout for the About tab, which includes a Markdown component for displaying content."""
    return html.Div(
        [
            dcc.Markdown(
                "Loading About…",
                id=ABOUT_MARKDOWN_ID,
                link_target="_blank",
            )
        ],
        style={"padding": "16px"},
    )
