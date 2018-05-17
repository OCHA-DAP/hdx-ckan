TRIGGER QUICK CHARTS VIA API
============================

When new recipes are built or data is improved, user needs to trigger quick charts with a script via API. The easiest solution is to use the api call *package_hxl_update*

HOW TO USE package_hxl_update ACTION
====================================

The action can be used via POST and it gets as parameter the id or name of the dataset. It returns the resource view dict list.


TECH DETAILS
------------

def package_hxl_update(context, data_dict):
    '''
    Checks every resource in a dataset to see if it has HXL tags.
    Adds the property "has_hxl_tags" as true on the resources that do.

    :param id:
    :type id: str
    :return: new resource view dict list
    :rtype: list
    '''


