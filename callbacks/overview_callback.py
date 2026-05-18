from urllib.parse import parse_qs, urlparse
from dash import Input, Output, State
import plotly.express as px
from utils.plot_chart import plot_two_pie_charts_px, plot_two_bar_charts_px
from utils.dashboard_settings import get_dashboard_settings, get_overview_metrics
from utils.plotly_download import build_plotly_download_config
from auth.models import normalize_series_color, pastel_continuous_palette
from utils.unit_handler import unit_detect


def _get_overview_metric_config(metric_title):
    """Return the selected overview metric plus all overview settings."""
    settings = get_dashboard_settings()
    overview_metrics = get_overview_metrics(settings)
    metric_map = {metric["title"]: metric for metric in overview_metrics}
    return metric_map.get(metric_title), overview_metrics, settings


def register_overview_callbacks(app, provider):
    """Register callbacks for overview metric selection, units, and chart rendering."""
    @app.callback(
        Output('scenario-dropdown', 'options'),
        Output('scenario-dropdown', 'value'),
    #     Input('tabs', 'value') 
        Input("url", "href"),
        State("scenario-dropdown", "value")
    )
    def update_scenario_dropdown(href, current_value):
        """Populate overview scenario options from the active study in the URL."""
        if not href:
            return [], None

        query = parse_qs(urlparse(href).query)
        study_id = query.get("study_id", [None])[0]

        if not study_id:
            return [], None

        try:
            study_id = int(study_id)
        except (TypeError, ValueError):
            return [], None

        scenarios = provider.get_scenarios_for_study(study_id)
        options = [{"label": scenario.name, "value": str(scenario.id)} for scenario in scenarios]
        print(current_value, "current_value")
        if current_value in [options[i]['value'] for i in range(len(options))]:
            value = current_value
        else:
            value = options[0]["value"] if options else None

        return options, value
    
    @app.callback(
        Output('metric-dropdown', 'options'),
        Output('metric-dropdown', 'value'),
        Input("url", "href"),
        State('metric-dropdown', 'value')
    )
    def update_metric_dropdown(_, current_value):
        """Populate overview metric options from dashboard settings."""
        settings = get_dashboard_settings()
        overview_metrics = get_overview_metrics(settings)
        options = [{"label": metric["title"], "value": metric["title"]} for metric in overview_metrics]
        option_values = {option["value"] for option in options}
        configured = settings.get("overview_metric")

        if current_value in option_values:
            value = current_value
        elif configured in option_values:
            value = configured
        else:
            value = options[0]["value"] if options else None

        return options, value

    @app.callback(
        Output('unit-dropdown-overview', 'options'),
        Output('unit-dropdown-overview', 'value'),
        Input('metric-dropdown', 'value'),
        State('unit-dropdown-overview', 'value')
    )
    def update_unit(metric, current_value):
        """Choose valid display-unit options for the selected overview metric."""
        metric_config, _, _ = _get_overview_metric_config(metric)
        if not metric_config:
            return [], None

        table_id = metric_config.get("table_id")
        df_unit = provider.get_labels(table_id)
        if not df_unit:
            return [], None

        label = df_unit[0]
        if label == "PJ":
            options = ['PJ', 'TWh', 'ktoe']
        elif label == "kt":
            options = ['kt', 'Mt']
        else:
            options = [label]

        if current_value in options:
            return options, current_value
        return options, options[0]
    

    @app.callback(
        Output('overview-chart', 'figure'),
        Output('overview-chart', 'config'),
        Input('scenario-dropdown', 'value'),
        Input('start-year-dropdown', 'value'),
        Input('end-year-dropdown', 'value'),
        Input('metric-dropdown', 'value'),
        Input('chart-type-overview-dropdown', 'value'),
        Input('unit-dropdown-overview', 'value')
    )
    def update_overview_chart(scenario, year_start, year_end, metric, chart_type, unit):
        """Render the overview chart for the selected metric, years, scenario, and unit."""
        scenario_name = provider.get_scenario_name(scenario)
        config = build_plotly_download_config(
            "overview",
            scenario_name,
            metric,
            year_start,
            year_end,
        )

        metric_config, _, _ = _get_overview_metric_config(metric)
        if not metric_config or not scenario or year_start is None or year_end is None:
            return px.bar(title="No overview metric available"), config

        table_id = metric_config.get("table_id")
        selected_series_titles = set(metric_config.get("series_titles") or [])
        divide_by = metric_config.get("divide_by") or 1.0

        if not table_id:
            return px.bar(title="Overview metric is missing its source table"), config

        label = unit
        data_base = provider.get_filtered_df(table_id, scenario, [year_start, year_start])
        data_selected = provider.get_filtered_df(table_id, scenario, [year_end, year_end])

        if selected_series_titles:
            data_base = data_base[data_base["seriesTitle"].isin(selected_series_titles)]
            data_selected = data_selected[data_selected["seriesTitle"].isin(selected_series_titles)]

        data_base = data_base.copy()
        data_selected = data_selected.copy()
        data_base["Value"] = data_base["Value"] / divide_by
        data_selected["Value"] = data_selected["Value"] / divide_by

        data_base = unit_detect(label, data_base)
        data_selected = unit_detect(label, data_selected)

        color_map = provider.get_series_color_map_by_title(table_id) if table_id else {}
        all_titles = list(dict.fromkeys(data_base["seriesTitle"].tolist() + data_selected["seriesTitle"].tolist()))
        fallback = pastel_continuous_palette(len(all_titles))
        for i, title in enumerate(all_titles):
            color = normalize_series_color(color_map.get(title))
            color_map[title] = color if color else fallback[i]

        if chart_type == 'pie':
            fig = plot_two_pie_charts_px(data_base, year_start, data_selected, year_end, metric, label, color_map=color_map)
        elif chart_type == 'bar':
            fig = plot_two_bar_charts_px(data_base, year_start, data_selected, year_end, metric, label, color_map=color_map)
        else:
            fig = px.bar(title=metric)

        return fig, config
