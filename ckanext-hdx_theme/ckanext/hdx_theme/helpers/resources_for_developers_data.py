access_hdx_by_api = {
    'title': 'Accessing HDX by API',
    'questions': [
        {
            'q': 'About the Humanitarian Data Exchange API',
            'a': 'This section contains information for developers who want to write code that interacts with the '
                 'Humanitarian Data Exchange (HDX) and the datasets it contains. Anything that you can do by way of '
                 'the HDX user interface, you can do programatically by making calls to the API and you can do a lot more. '
                 'Typical uses of the API might be to script the creation and update of datasets in HDX or to read '
                 'data for analysis and visualisation.',
        },
        {
            'q': 'Programming Language Support ',
            'a': 'HDX has a RESTful API largely unchanged from the underlying CKAN API which can be used from any '
                 'programming language that supports HTTP GET and POST requests. However, the terminology that CKAN '
                 'uses is a little different to the HDX user interface. Hence, we have developed wrappers for specific '
                 'languages that harmonise the nomenclature and simplify the interaction with HDX. '
                 '<br/>'
                 'These APIs allow various operations such as searching, reading and writing dataset metadata, but not '
                 'the direct querying of data within resources which can point to files or urls and of which there can '
                 'be more than one per dataset.',
        },
        {
            'q': 'Python',
            'a': 'The recommended way of developing against HDX is to use the <a href="https://github.com/OCHA-DAP/hdx-python-api" target="_blank">HDX Python API</a>. This is a mature library that supports Python 2.7 and 3 with tests that have a high level of code coverage. The major goal of the library is to make pushing and pulling data from HDX as simple as possible for the end user. There are several ways this is achieved. It provides a simple interface that communicates with HDX using the CKAN Python API, a thin wrapper around the CKAN REST API. The HDX objects, such as datasets and resources, are represented by Python classes. This should make the learning curve gentle and enable users to quickly get started with using HDX programmatically. For example, to read a dataset and get its resources, you would simply do: <br/> '
                 '<pre><code class="python">'
                 'from hdx.hdx_configuration import Configuration <br/>'
                 'from hdx.data.dataset import Dataset</br>'
                 'Configuration.create(hdx_site=\'prod\', user_agent=\'A_Quick_Example\', hdx_read_only=True)\'<br/>'
                 'dataset = Dataset.read_from_hdx(\'reliefweb-crisis-app-data\')<br/>'
                 'resources = dataset.get_resources()<br/>'
                 '</code></pre>'
                 'There is <a href="http://ocha-dap.github.io/hdx-python-api/" target="_blank">library API-level '
                 'documentation</a> available online.'
                 '<br/>'
                 'If you intend to push data to HDX, then it may be helpful to start with this '
                 '<a target="_blank" href="https://github.com/OCHA-DAP/hdxscraper-template">scraper template</a> which '
                 'shows what needs to be done to create datasets on HDX. It should be straightforward to adapt the '
                 'template for your needs.',
        },
        {
            'q': 'R',
            'a': 'If you wish to read data from HDX for analysis in R, then you can use the '
                 '<a href="https://gitlab.com/dickoa/rhdx" target="_blank">rhdx</a> package. '
                 'The goal of this package is to provide a simple interface to interact with HDX. Like the '
                 'Python API, it is a wrapper around the CKAN REST API. rhdx is not yet fully mature and '
                 'some breaking changes are expected.',
        },
        {
            'q': 'REST',
            'a': 'If you need to use another language or simply want to examine dataset metadata in detail in your '
                 'web browser, then you can use '
                 '<a target="_blank" href="http://docs.ckan.org/en/ckan-2.6.3/api/index.html">CKAN\'s RESTful API</a>, '
                 'a powerful, RPC-style interface that exposes all of CKAN\'s core features to clients.',
        }
    ]
}

coding_hxl = {
    'title': 'Coding with the Humanitarian Exchange Language',
    'questions': [
        {
            'q': 'About the Humanitarian Exchange Language',
            'a': 'This section contains information for developers who want to write code to process datasets that '
                 'use the Humanitarian Exchange Language (HXL). HXL is a different kind of data standard, '
                 'adding hashtags to existing datasets to improve information sharing during a humanitarian crisis '
                 'without adding extra reporting burdens. HXL has its '
                 '<a target="_blank" href="http://hxlstandard.org/">own website</a> and of particular interest '
                 'will be the '
                 '<a target="_blank" href="http://hxlstandard.org/standard">documentation</a> section.',
        },
        {
            'q': 'Python',
            'a': 'The most well developed HXL library, '
                 '<a target="_blank" href="https://github.com/HXLStandard/libhxl-python">libhxl-python</a>, '
                 'is written in Python. The most recent versions support Python 3 only, but there are earlier versions '
                 'with Python 2.7 support. Features of the library include filtering, validation and the ingestion and '
                 'generation of various formats. libhxl-python uses an idiom that is familiar from JQuery and other '
                 'Javascript libraries; for example, to load a dataset, you would use simply'
                 '<pre><code>'
                 'import hxl <br/>'
                 'source = hxl.data(\'http://example.org/dataset.xlsx\')'
                 '</code></pre>'
                 'As in JQuery, you process the dataset by adding additional steps to the chain. The following example '
                 'selects every row with the organisation "UNICEF" and removes the column with email addresses:'
                 '<pre><code>source.with_rows(\'#org=UNICEF\').without_columns(\'#contact+email\')</code></pre>'
                 'The library also includes a set of command-line tools for processing HXL data in shell scripts. For '
                 'example, the following will perform the same operation shown above, without the need to write Python code:'
                 '<pre><code>$ cat dataset.xlsx | hxlselect -q "#org=UNICEF" | hxlcut -x \'#contact+email\'</code></pre>'
                 'There is library '
                 '<a target="_blank" href="http://hxlstandard.github.io/libhxl-python/">API-level documentation</a> '
                 'available online.',
        },
        {
            'q': 'Javascript',
            'a': '<a target="_blank" href="https://github.com/HXLStandard/libhxl-js">libhxl-js</a> is a library '
                 'for HXL written in Javascript. It supports high-level filtering and aggregation operations on HXL '
                 'datasets. Its programming idiom is similar to libhxl-python, but it is smaller and contains fewer '
                 'filters and no data-validation support.',
        },
        {
            'q': 'R',
            'a': 'Third party support for R is available via the package '
                 '<a target="_blank" href="https://github.com/dirkschumacher/rhxl">rhxl</a>. It has basic support for '
                 'reading HXLated files to make them available for advanced data-processing and analytics inside R.',
        }
    ]
}

tools= {
    'title': 'Tools',
    'questions': [
        {
            'q': 'HDX Tools',
            'a': 'HDX provides a '
                 '<a target="_blank" href="https://tools.humdata.org/">suite of tools</a> that leverage HXLated '
                 'datasets:'
                 '<ol>'
                 '<li> '
                    'QuickCharts automatically generates embeddable, live data charts, graphs and key figures from '
                    'your data. It uses the HXL hashtags to guess the best charts to display, but you can then go in '
                    'and override with your own '
                    '<a target="_blank" href="https://github.com/OCHA-DAP/hxl-recipes">preferences</a>.'
                 '</li>'
                 '<li> '
                    'HXL Tag Assist allows you to find hashtag examples and definitions, and see how data managers are '
                    'using the hashtags in their data. '
                 '</li> '
                 '<li> '
                    'Data Check provides help with data cleaning for humanitarian data, automatically detecting and '
                    'highlighting common errors. It includes validation against CODs and other vocabularies.'
                 '</li>'
                 '</ol>',
        },
        {
            'q': 'HXL Proxy',
            'a': 'The <a target="_blank" href="https://proxy.hxlstandard.org/">HXL Proxy</a> is a tool for validating, '
                 'cleaning, transforming, and visualising HXL-tagged data. You supply an input url pointing to a '
                 'tabular or JSON dataset and then create a recipe that contains a series of steps for transforming '
                 'the data. The result is a download link that you can share and use in HDX, and the output will '
                 'update automatically whenever the source dataset changes. Full user documentation is '
                 'available in the '
                 '<a target="_blank" href="https://github.com/HXLStandard/hxl-proxy/wiki">HXL Proxy wiki</a>.'
                 '<br/>'
                 'The HXL Proxy is primarily a web wrapper around the libhxl-python library (see above), and makes '
                 'the same functionality available via '
                 '<a target="_blank" href="https://en.wikipedia.org/wiki/Representational_state_transfer">RESTful</a> '
                 'web calls.',
        }
    ]
}

other_hdx_libraries = {
    'title': 'Other HDX Libraries',
    'questions': [
        {
            'q': 'HDX Python Country',
            'a': 'Humanitarian projects frequently require handling countries, locations and regions in particular '
                 'dealing with inconsistent country naming between different data sources and different coding '
                 'standards like ISO3 and M49. The '
                 '<a target="_blank" href="https://github.com/OCHA-DAP/hdx-python-country">HDX Python Country</a> '
                 'library was created to fulfill these requirements and is a dependency of the HDX Python API. '
                 'It is also very useful as a standalone library and has '
                 '<a target="_blank" href="https://ocha-dap.github.io/hdx-python-country/">library API-level documentation</a> '
                 'available online.'
        },
        {
            'q': 'HDX Python Utilities',
            'a': 'All kinds of utility functions have been coded over time for use internally, so since we think '
                 'these have value externally, it was decided that they should be packaged into the '
                 '<a target="_blank" href="https://github.com/OCHA-DAP/hdx-python-utilities">HDX Python Utilities</a> '
                 'library which has library API-level documentation available online.',
        }
    ]
}


contact = {
    'title': 'Contact Us',
    'questions': [
        {
            'q': 'How do I contact the HDX team?',
            'a': 'If you have any questions about these resources, we will do our best to answer them. We '
                 'would also love to hear about how you are using them for your work.<br/>'
                 '<br/>'
                 'Please contact us at: <a href="mailto:hdx@un.org">hdx@un.org</a>. '
                 'Sign up to receive our '
                 '<a target="_blank"  href="http://humdata.us14.list-manage1.com/subscribe?u=ea3f905d50ea939780139789d&id=99796325d1">newsletter here</a>.',
        },
    ]
}



rfd_data = [
    access_hdx_by_api,
    coding_hxl,
    tools,
    other_hdx_libraries,
    contact
]
