
def compute_simplifying_units(value):
    '''

    :param value:
    :type value: float
    :return: bln, mln, k depending on how big the value is
    :rtype: str
    '''

    unit = 'count'

    if value > 1000000000.0:
        unit = 'bln'
    elif value > 1000000.0:
        unit = 'mln'
    elif value > 1000.0:
        unit = 'k'

    return unit