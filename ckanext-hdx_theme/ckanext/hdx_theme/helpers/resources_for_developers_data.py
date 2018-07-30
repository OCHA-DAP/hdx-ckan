access_hdx_by_api = {
    'title': 'Accessing HDX by API',
    'questions': [
        {
            'q': 'About the Humanitarian Data Exchange API',
            'a': 'This section contains information for developers who want to write code that interacts with the Humanitarian Data Exchange (HDX) and the datasets it contains. Anything that you can do by way of the HDX user interface, you can do programatically by making calls to the API and you can do a lot more. Typical uses of the API might be to script the creation and update of datasets in HDX or to read data for analysis and visualisation.',
        },
        {
            'q': 'Programming Language Support ',
            'a': 'HDX has a RESTful API largely unchanged from the underlying CKAN API which can be used from any programming language that supports HTTP GET and POST requests. However, the terminology that CKAN uses is a little different to the HDX user interface. Hence, we have developed wrappers for specific languages that harmonise the nomenclature and simplify the interaction with HDX. These APIs allow various operations such as searching, reading and writing dataset metadata, but not the direct querying of data within resources which can point to files or urls and of which there can be more than one per dataset.',
        },
        {
            'q': 'Python',
            'a': 'The recommended way of developing against HDX is to use the HDX Python API. This is a mature library that supports Python 2.7 and 3 with tests that have a high level of code coverage. The major goal of the library is to make pushing and pulling data from HDX as simple as possible for the end user. There are several ways this is achieved. It provides a simple interface that communicates with HDX using the CKAN Python API, a thin wrapper around the CKAN REST API. The HDX objects, such as datasets and resources, are represented by Python classes. This should make the learning curve gentle and enable users to quickly get started with using HDX programmatically. For example, to read a dataset and get its resources, you would simply do: <br/> '
                 'from hdx.hdx_configuration import Configuration'
                 'from hdx.data.dataset import Dataset'
                 'Configuration.create(hdx_site=\'prod\', user_agent=\'A_Quick_Example\', hdx_read_only=True)\''
                 'dataset = Dataset.read_from_hdx(\'reliefweb-crisis-app-data\')'
                 'resources = dataset.get_resources()</br>'
                 'There is library API-level documentation available online.',
        },
        {
            'q': 'R',
            'a': 'If you wish to read data from HDX for analysis in R, then you can use the rhdx package. The goal of this package is to provide a simple interface to interact with HDX. Like the Python API, it is a wrapper around the CKAN REST API. rhdx is not yet fully mature and some breaking changes are expected.',
        },
        {
            'q': 'REST',
            'a': 'If you need to use another language or simply want to examine dataset metadata in detail in your web browser, then you can use CKAN\'s RESTful API, a powerful, RPC-style interface that exposes all of CKAN\'s core features to clients.',
        }
    ]
}

coding_hxl = {
    'title': 'Coding with the Humanitarian Exchange Language',
    'questions': [
        {
            'q': 'About the Humanitarian Exchange Language',
            'a': 'This section contains information for developers who want to write code to process datasets that use the Humanitarian Exchange Language (HXL). HXL is a different kind of data standard, adding hashtags to existing datasets to improve information sharing during a humanitarian crisis without adding extra reporting burdens. HXL has its own website and of particular interest will be the documentation section.',
        },
        {
            'q': 'Python',
            'a': 'The most well developed HXL library, libhxl-python, is written in Python. The most recent versions support Python 3 only, but there are earlier versions with Python 2.7 support. Features of the library include filtering, validation and the ingestion and generation of various formats. libhxl-python uses an idiom that is familiar from JQuery and other Javascript libraries; for example, to load a dataset, you would use simply',
        },
        {
            'q': 'Javascript',
            'a': 'libhxl-js is a library for HXL written in Javascript. It supports high-level filtering and aggregation operations on HXL datasets. Its programming idiom is similar to libhxl-python, but it is smaller and contains fewer filters and no data-validation support.',
        },
        {
            'q': 'R',
            'a': 'Third party support for R is available via the package rhxl. It has basic support for reading HXLated files to make them available for advanced data-processing and analytics inside R.',
        }
    ]
}

tools= {
    'title': 'Tools',
    'questions': [
        {
            'q': 'HDX Tools',
            'a': 'HDX provides a suite of tools that leverage HXLated datasets:'
                 '<ol>'
                 '<li> QuickCharts automatically generates embeddable, live data charts, graphs and key figures from your data. It uses the HXL hashtags to guess the best charts to display, but you can then go in and override with your own preferences.</li>'
                 '<li> HXL Tag Assist allows you to find hashtag examples and definitions, and see how data managers are using the hashtags in their data. </li> '
                 '<li> Data Check provides help with data cleaning for humanitarian data, automatically detecting and highlighting common errors. It includes validation against CODs and other vocabularies.</li>'
                 '</ol>',
        },
        {
            'q': 'HXL Proxy',
            'a': 'The HXL Proxy is a tool for validating, cleaning, transforming, and visualising HXL-tagged data. You supply an input url pointing to a tabular or JSON dataset and then create a recipe that contains a series of steps for transforming the data. The result is a download link that you can share and use in HDX, and the output will update automatically whenever the source dataset changes. Full user documentation is available in the HXL Proxy wiki.<br/>'
                 'The HXL Proxy is primarily a web wrapper around the libhxl-python library (see above), and makes the same functionality available via RESTful web calls.',
        }
    ]
}

other_hdx_libraries = {
    'title': 'Other HDX Libraries',
    'questions': [
        {
            'q': 'HDX Python Country',
            'a': 'Humanitarian projects frequently require handling countries, locations and regions in particular dealing with inconsistent country naming between different data sources and different coding standards like ISO3 and M49. The HDX Python Country library was created to fulfill these requirements and is a dependency of the HDX Python API. It is also very useful as a standalone library and has library API-level documentation available online.'
        },
        {
            'q': 'HDX Python Utilities',
            'a': 'All kinds of utility functions have been coded over time for use internally, so since we think these have value externally, it was decided that they should be packaged into the HDX Python Utilities library which has library API-level documentation available online.',
        }
    ]
}


contact = {
    'title': 'Contact Us',
    'questions': [
        {
            'q': 'How do I contact the HDX team?',
            'a': 'For general enquiries, e-mail <a href="mailto:hdx@un.org">hdx@un.org</a>. If you see an issue with '
                 'the site, e-mail <a href="mailto:hdx.feedback@gmail.com">hdx.feedback@gmail.com</a>. You can also '
                 'reach us on Twitter at <a target="_blank" href="https://twitter.com/humdata">@humdata</a>. Sign up '
                 'to receive our blog posts '
                 '<a target="_blank"  href="http://humdata.us14.list-manage.com/subscribe?u=ea3f905d50ea939780139789d&id=99796325d1">here</a>.',
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
