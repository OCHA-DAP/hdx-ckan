

downloadable_formats = {
    'csv', 'xls', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip'
}

def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False
