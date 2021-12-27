def find_approx_download(exact_downloads):
    '''

    :param exact_downloads: the total number of downloads
    :type exact_downloads: int
    :return: something like 1000+
    :rtype: int
    '''

    if exact_downloads >= 10 and exact_downloads < 100:
        divider = 10
    # for 9999 we want 9900+
    elif exact_downloads >= 100 and exact_downloads < 10000:
        divider = 100
    elif exact_downloads >= 10000:
        divider = 1000
    else:
        return 0

    return (exact_downloads // divider) * divider
