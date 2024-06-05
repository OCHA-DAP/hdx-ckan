CONSTANTS = {
    'HERO_SECTION_TITLE': '''The HDX Humanitarian API (HAPI) is a way to access standardised indicators from multiple sources to automate workflows and visualisations''',
    'HERO_SECTION_DESCRIPTION': '''HDX HAPI is in beta phase, and we are seeking feedback. To share your thoughts or join our slack channel, send an email to <a href="{0}" title="Contact us">hdx@un.org</a>.''',

    'DATA_COVERAGE_SECTION_TITLE': '''Data Coverage''',
    'DATA_COVERAGE_SECTION_DESCRIPTION': '''Our initial coverage aligns with the data included in the <a href="{0}" target="_blank" data-module="hdx_click_stopper" data-module-link_type="hapi data coverage description" title="HDX Data Grids">HDX Data Grids</a>, which places the most important crisis data into six categories and 20 sub-categories. Our beta version of HDX HAPI covers 57 indicators across 25 locations that have a <a href="{1}" target="_blank" title="Humanitarian Response Plan" data-module="hdx_click_stopper" data-module-link_type="hapi data coverage description">Humanitarian Response Plan</a>.''',
    'DATA_COVERAGE_SECTION_PARAGRAPH': '''Refer to the <a href="{0}" target="_blank" data-module="hdx_click_stopper" data-module-link_type="hapi data coverage description" title="HAPI - The Humanitarian API">documentation</a> for the latest coverage. <a href="{1}" data-module="hdx_click_stopper" data-module-link_type="hapi data coverage description" title="Contact us">Contact us</a> to request additional indicators in future versions of HDX HAPI.''',

    'BE_INSPIRED_SECTION_TITLE': '''Be Inspired''',
    'BE_INSPIRED_SECTION_DESCRIPTION': '''Take a look at visualisations and code examples''',

    'BE_INSPIRED_CARD_TITLE_POWER_BI': '''Power BI workflow''',
    'BE_INSPIRED_CARD_TEXT_POWER_BI': '''A tutorial to demonstrate how easy it is to bring in data.''',
    'BE_INSPIRED_CARD_BUTTON_POWER_BI': '''Learn more''',
    'BE_INSPIRED_CARD_BUTTON_LINK_POWER_BI': '''https://docs.google.com/presentation/d/19HfMI9gnKXAMhe0SFZdbbUFesNnTnfeUI9rnshN2kkk/edit#slide=id.g2ddc745d4a3_0_81''',

    'BE_INSPIRED_CARD_TITLE_API': '''API Sandbox''',
    'BE_INSPIRED_CARD_TEXT_API': '''A sandbox environment to help construct queries and get a data response.''',
    'BE_INSPIRED_CARD_BUTTON_API': '''Learn more''',
    'BE_INSPIRED_CARD_BUTTON_LINK_API': '''https://stage.hapi-humdata-org.ahconu.org/docs#/Locations%20and%20Administrative%20Divisions/get_locations_api_v1_metadata_location_get''',

    'BE_INSPIRED_CARD_TITLE_VISUALIZATION': '''Visualisation''',
    'BE_INSPIRED_CARD_TEXT_VISUALIZATION': '''A dashboard with a selection of key figures, charts and a map for all countries in HDX HAPI.''',
    'BE_INSPIRED_CARD_BUTTON_VISUALIZATION': '''Learn more''',
    'BE_INSPIRED_CARD_BUTTON_LINK_VISUALIZATION': '''https://baripembo.github.io/viz-datagrid-dashboard/#''',

    'BE_INSPIRED_CARD_TITLE_CHATBOT': '''Chatbot''',
    'BE_INSPIRED_CARD_TEXT_CHATBOT': '''An early stage AI chatbot developed with DataKind to ask questions about the data.''',
    'BE_INSPIRED_CARD_BUTTON_CHATBOT': '''Learn more''',
    'BE_INSPIRED_CARD_BUTTON_LINK_CHATBOT': '''#''',

    'FAQ_SECTION_TITLE': '''FAQ''',

    'PARTNERS_SECTION_TITLE': '''Partners''',
}

DATA_COVERAGE_CONSTANTS = [
    {
        "category": "Affected People",
        "subcategory": "Humanitarian Needs Overview",
        "contributor": "OCHA offices",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-humanitarian-needs"
    },
    {
        "category": "Affected People",
        "subcategory": "Refugees and Persons of Concern",
        "contributor": "UN Refugee Agency (UNHCR)",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-refugees-persons-of-concern"
    },
    {
        "category": "Coordination & Context",
        "subcategory": "Conflict Events",
        "contributor": "The Armed Conflict Location & Event Data Project (ACLED)",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-conflict-events"
    },
    {
        "category": "Coordination & Context",
        "subcategory": "Funding",
        "contributor": "OCHA Financial Tracking System (FTS)",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-funding"
    },
    {
        "category": "Coordination & Context",
        "subcategory": "National Risk",
        "contributor": "INFORM",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-national-risk"
    },
    {
        "category": "Coordination & Context",
        "subcategory": "Operational Presence (Who-is-doing-what-where)",
        "contributor": "OCHA offices",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-operation-presence-3w-who-is-doing-what-where"
    },
    {
        "category": "Food Security & Nutrition",
        "subcategory": "Food Prices",
        "contributor": "World Food Programme (WFP)",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-food-prices"
    },
    {
        "category": "Food Security & Nutrition",
        "subcategory": "Food Security",
        "contributor": "The Integrated Food Security Phase Classification (IPC)",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-food-security"
    },
    {
        "category": "Population & Socio-economy",
        "subcategory": "Population",
        "contributor": "United Nations Population Fund (UNFPA) and OCHA offices",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-baseline-population"
    },
    {
        "category": "Population & Socio-economy",
        "subcategory": "Poverty Rate",
        "contributor": "The Oxford Poverty and Human Development Initiative (OPHI)",
        "link": "https://hdx-hapi.readthedocs.io/en/latest/subcategory_details/#sub-category-poverty-rate"
    }
]

SECTIONS_CONSTANTS = [
    {'name': 'Data Coverage', 'url': '#data-coverage'},
    {'name': 'Be Inspired', 'url': '#be-inspired'},
    {'name': 'FAQ', 'url': '#faq'},
    {'name': 'Read the documentation', 'url': 'https://hdx-hapi.readthedocs.io/'},
]
