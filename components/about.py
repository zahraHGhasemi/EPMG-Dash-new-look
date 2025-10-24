from dash import html
import dash_bootstrap_components as dbc
from dash import html, dcc

def generate_accordion_items(data_list):
    """
    Takes a list of strings or dicts and returns dbc.AccordionItems.
    """
    items = []
    for i, data in enumerate(data_list):
        # You can customize this content easily
        items.append(
            dbc.AccordionItem(
                title=f"Item {i+1}",
                children=[
                    html.P(f"Content: {data}")
                ]
            )
        )
    return items


# --- Example data ---
class StudySection:
    def __init__(self, title, image=None, items=None):
        """
        title: str - Accordion item title
        image: str | None - Image URL or path
        items: list - List of Dash HTML components (html.P, html.Ul, etc.)
        """
        self.title = title
        self.image = image
        self.items = items or []

    def to_accordion_item(self):
        """Return a dbc.AccordionItem built from the content."""
        content = []
        content.extend(self.items)  # Add whatever HTML components were passed in
        if self.image:
            content.append(
                html.Img(
                    src=self.image,
                    style={
                        "width": "100%",          # scales with container
                        "borderRadius": "8px",
                        "marginBottom": "10px",
                        "minWidth": "300px",      # minimum width
                        "minHeight": "200px",     # minimum height
                        "maxWidth": "600px",      # maximum width
                        "maxHeight": "400px",     # maximum height
                        "objectFit": "contain"    # maintain aspect ratio
                    }
                )
            )
        return dbc.AccordionItem(title=self.title, children=content)


# --- Create your data ---
sections = [
    StudySection(
        title="Background",
        image=None,
        items=[
            html.P("UCC’s Energy Policy and Modelling Group (EPMG) is supporting the Climate Change Advisory Council (CCAC) as part of the Carbon Budgets Working Group (CBWG) in the Council’s statutory role of making recommendations to Government for carbon budgets 3 (covering 2031-35) and carbon budget 4 (2034-40), by the end of 2024. The CBWG is tasked with developing an evidence base for the Council’s carbon budget proposals, including the provision of modelling and analytical support."),
            html.P("As part of this process, the EPMG is modelling future potential pathways for Ireland’s energy system consistent with different levels of decarbonisation ambition, covering energy supply, electricity, transport, buildings and industry. The purpose of these scenarios is to indicate the pace and depth of change across the energy system necessary to meet different levels of mitigation ambition, including the timing of introducing new technologies, indicating the reliance on speculative technologies, and the role of energy demand reduction."),
            html.P("The EPMG has already produced two modelling iterations in December 2023 and June 2024, and has undertaken rounds of stakeholder engagement, and adopted feedback from the CCAC following each iteration."),
            html.P("This webpage includes detailed results for the final iteration of modelled scenarios, presented to the CBWG in August 2024. A detailed accompanying technical report was submitted to the CCAC in October 2024 and was published by the CCAC (link) along with its full carbon budget recommendations in December 2024 (link).")
        ]
    ),
    StudySection(
        title="Scenario assumptions",
        image="/assets/scenarios.png",
        items=[
            html.P("The TIM scenarios incorporate two types of carbon budget constraints for different periods:"),
            html.P(
                "(1) CB 2021–2050: This is the overall carbon budget constraint that sets the "
                "maximum allowable CO₂ emissions from energy systems for the period 2021 to 2050."
            ),
            html.P("Five different Carbon Budgets (CB) for the period 2021–2050 are modelled:"),
            html.Ul([
                html.Li("450 Mt CO₂"),
                html.Li("400 Mt CO₂"),
                html.Li("350 Mt CO₂"),
                html.Li("300 Mt CO₂"),
                html.Li("250 Mt CO₂"),
            ]),
            html.P(
                "The specified amount reflects the limits in scenario names. "
                "For example, the 350 Mt scenario assumes a maximum of 350 million tonnes "
                "of CO₂ emissions from energy systems from 2021 to 2050."
            ),
            html.P("(2) CB 2021-2030: This budget represents the maximum allowable CO2 emissions from energy systems for the period 2021 to 2030. In core scenarios, it is assumed that Sectoral Emissions Ceilings (SECs) are met, as outlined in the Table 3.2 Climate Action Plan. The total SECs for the periods 2021-2025 and 2026-2030 have a maximum limit of 275 Mt of CO2 and is fixed across all carbon budget scenarios, apart from WEM and WAM scenarios. In these scenarios, it is assumed that there is an overshoot of the SECs in the period to 2030 according to the emissions as projected by the Environmental Protection Agency, under current and planned policies.The figure below shows the CB allocations for various scenarios. In the 250Mt scenario, the CB allocated for 2021-2030 is greater than the total budget for the entire period from 2021 to 2050. The model has limited ability to counterbalance emissions with a negative emissions technology, Bioenergy with Carbon Capture and Storage (BECCS). If in a given scenario the model cannot deliver a given carbon budget considering all the constraints applied, then a backstop negative emissions technology is deployed, at a cost of €2000 per tonne of CO2.")
        ]
    ),
    StudySection(
        title="Core scenarios",
        image=None,
        items=[
            html.P("These scenarios have an overall carbon budget of 250Mt to 450Mt applied from 2021 to 2050. All five CB scenarios are modeled using a business-as-usual (BAU) demand projection and do not have a suffix, such as 250Mt.")
        ]
    ),
    StudySection(
        title="Other scenarios",
        image=None,
        items=[
            html.Ul([
                html.Li([
                    html.B("Low Energy Demand (LED): "),
                    html.P(
                        "Four of the lower CBs are modelled using a LED projection. "
                        "They have LED suffixes such as 250Mt-LED. For the detailed assumptions of "
                        "LED scenarios see Gaur et al. (2022) Article."
                    ),
                ])
            ]),
            html.Ul([
                html.Li([
                    html.B("WAM & WEM: "),
                    html.P(
                        "In these scenarios, emissions projections from the Environmental Protection Agency "
                        "are used as the lower bound for emissions in the pre-2030 period."
                    ),
                ])
            ]),
            html.Ul([
                html.Li([
                    html.P(
                        "However, the overall CBs remain the same for the 2021–2050 period, using BaU energy demand "
                        "projections. For example, 350Mt-WEM indicates an overall carbon budget of 350 million tonnes "
                        "for 2021 to 2050 and 310 million tonnes for 2021 to 2030."
                    ),
                ])
            ]),
            html.Ul([
                html.Li([
                    html.B("LowBio: "),
                    html.P(
                        "This scenario group restricts biomass imports to current levels and no increase is allowed "
                        "beyond the existing import levels, such as 250Mt-LowBio."
                    ),
                ])
            ]),
            html.Ul([
                html.Li([
                    html.B("HighSolarPV: "),
                    html.P(
                        "This scenario significantly increases solar PV adoption, with the maximum allowable capacity "
                        "rising from 10 GW in the core scenarios to 18 GW."
                    ),
                ])
            ]),
            html.Ul([
                html.Li([
                    html.B("Weighted average scenario: "),
                    html.P(
                        "This scenario represents an energy sector pathway consistent with carbon budgets "
                        "(approved and legally adopted to 2030 and proposed to 2040). It is a composite scenario "
                        "constructed by averaging energy sector trajectories across the fifteen shortlisted scenarios "
                        "in the CCAC’s Carbon Budget Proposal Report, which informed the proposed third and fourth "
                        "carbon budgets. It reflects a weighted average of the 300Mt, 300Mt-LED, 300Mt-LowBio, "
                        "350Mt, 350Mt-LED, 350Mt-LowBio scenarios, weighted according to their frequency in the shortlist."
                    ),
                ])
            ]),
        ]
    ),
    StudySection(
        title="References",
        items=[
            html.P([
                html.B("TIM Documentation Paper: "),
                "O. Balyk et al., “TIM: Modelling pathways to meet Ireland’s long-term energy system challenges with the TIMES-Ireland Model (v1.0)” Geoscientific Model Development, vol. 15, 2022 ",
                html.A("Link", href="https://gmd.copernicus.org/articles/15/4991/2022/", target="_blank")
            ]),
            html.P([
                html.B("TIM Application Papers")
            ]),
            html.P([
                "Accelerated vs Delayed Climate Action: V. Aryanpur et al., “Implications of accelerated and delayed climate action for Ireland’s energy transition under carbon budgets” Nature Portfolio, npj Climate Action, vol. 3, 2024 ",
                html.A("Link", href="https://www.nature.com/articles/s44168-024-00181-7", target="_blank")
            ]),
            html.P([
                "Decarbonising Trucks: V. Aryanpur, F. Rogan, “Decarbonising road freight transport: The role of zero-emission trucks and intangible costs” Nature Scientific Reports, vol. 14, 2024 ",
                html.A("Link", href="https://www.nature.com/articles/s41598-024-52682-4", target="_blank")
            ]),
            html.P([
                "District Heating: J. Mc Guire et al., “Is District Heating a cost-effective solution to decarbonise Irish buildings?” Energy, vol. 296, 2024 ",
                html.A("Link", href="https://www.sciencedirect.com/science/article/pii/S036054422400882X", target="_blank")
            ]),
            html.P([
                "Decarbonising Private Cars: V. Aryanpur et al., “Decarbonisation of passenger light-duty vehicles using spatially resolved TIMES-Ireland Model” Applied Energy, vol. 316, 2022 ",
                html.A("Link", href="https://www.sciencedirect.com/science/article/pii/S0306261922004676", target="_blank")
            ]),
            html.P([
                "Low Energy Demand: A. Gaur et al., “Low energy demand scenario for feasible deep decarbonisation: Whole energy systems modelling for Ireland” Renewable Sustainable Energy Transition, 2022 ",
                html.A("Link", href="https://www.sciencedirect.com/science/article/pii/S2667095X22000083", target="_blank")
            ]),
            html.P([
                "Residential Sector: J. Mc Guire et al., “Developing decarbonisation pathways in changing TIMES for Irish homes” Energy Strategy Reviews, vol. 47, 2022 ",
                html.A("Link", href="https://www.sciencedirect.com/science/article/pii/S2211467X23000366", target="_blank")
            ]),
            html.P([
                "Power Sector: X. Yue et al., “Least cost energy system pathways towards 100% renewable energy in Ireland by 2050” Energy, vol. 207, 2020 ",
                html.A("Link", href="https://www.sciencedirect.com/science/article/pii/S0360544220313712", target="_blank")
            ]),
        ]
    )
    ,
    StudySection(
        title = "Model and Data Availability",
        items = [
            html.P(["The model and all underpinning data used in this research are publicly available on ",html.A("GitHub", href ="https://github.com/MaREI-EPMG/times-ireland-model/tree/v1.1.0", target = "_blank") ,", and a complete archive of all output tables from this webpage are available to download in CSV form on ", html.A("Zenodo", href = "https://zenodo.org/records/14337533", target= "_blank"), "."])
        ]
    ),
    StudySection(
        title = "ACKNOWLEDGEMENTS",
        items = [
            html.P("We acknowledge and are grateful for the contributions of past and current members of UCC’s Energy Policy and Modelling Group, particularly those who contributed to the development of TIM and its predecessor, the TIMES-Ireland Model. We are also thankful to the CCAC and members of the CBWG, particularly SEAI’s energy modelling team and Prof. John FitzGerald, for constructive feedback on previous iterations of this research. This research was part-funded by the Department of Environment, Climate and Communications through the CAPACITY project.")
        ]
    )

]
# --- Create the accordion ---
accordion_items = [section.to_accordion_item() for section in sections]

def about_layout():
    return(html.Div([
        dbc.Container(
            [
                html.H3("CARBON BUDGET ANALYSIS WITH THE TIMES-IRELAND MODEL (TIM)", className="mb-4"),
                html.H4("Third iteration of modelling to support CCAC Carbon Budgets Working Group"),
                dbc.Accordion(
                    accordion_items ,
                    always_open=True,
                    id="study-accordion"
                )
            ],
            className="p-4",
            fluid=True
        )

    ])
    )
    