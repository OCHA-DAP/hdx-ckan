EAA_EDUCATION_FACILITIES = {'buildings', 'education facilities - schools', 'facilities and infrastructure'}

EAA_EDUCATION_STATISTICS = {
    'baseline population', 'census', 'demographics', 'development', 'early learning', 'economics',
    'educational attainment', 'educators - teachers', 'gap analysis', 'government data', 'indicators', 'inequality',
    'literacy', 'mortality', 'out-of-school', 'poverty', 'school enrollment', 'sex and age disaggregated data - sadd',
    'socioeconomics', 'survey', 'sustainable development',
}

EAA_CRISIS_RESPONSE = {
    'access to education', 'affected schools', 'aid workers security', 'armed violence', 'assistance targets',
    'Bangladesh - Rohingya refugee crisis', 'camp coordination and camp management', 'caseload - humanitarian profile',
    'casualties', 'complex emergency', 'common operational dataset - cod', 'coordination', 'coxs bazar',
    'cyclones - hurricanes - typhoons', 'damage assessment', 'damaged buildings',
    'displaced persons locations - camps - shelters', 'earthquakes', 'ebola', 'epidemics and outbreaks',
    'fatalities - deaths', 'floods'
}

EAA_ALL_USED_TAGS = EAA_EDUCATION_FACILITIES.union(EAA_EDUCATION_STATISTICS).union(EAA_CRISIS_RESPONSE)

EAA_FACET_NAMING_TO_INFO = {
    'education_facilities': {
        'url_param_name': 'ext_eaa_education_facilities',
        'tag_list': EAA_EDUCATION_FACILITIES,
        'negate': False
    },
    'education_statistics': {
        'url_param_name': 'ext_eaa_education_statistics',
        'tag_list': EAA_EDUCATION_STATISTICS,
        'negate': False
    },
    'crisis_response': {
        'url_param_name': 'ext_eaa_crisis_response',
        'tag_list': EAA_CRISIS_RESPONSE,
        'negate': False
    },
    'other': {
        'url_param_name': 'ext_eaa_other',
        'tag_list': EAA_ALL_USED_TAGS,
        'negate': True
    }
}

