from netaddr import iter_iprange

__virtualname__ = 'netutils'


def __virtual__():
    return __virtualname__


def parse_network_ranges(ranges, needed):
    '''
    Takes comma seprated list of IP ranges and returns full list of IP addresses in these ranges.
    Second argument is used to check if there is enough IP addresses to cover the required number of nodes.

    >>> parse_network_ranges("192.168.1.101-192.168.1.103,192.168.2.101-192.168.2.103")
    ["192.168.1.101", "192.168.1.102", "192.168.1.103", "192.168.2.101", "192.168.2.102", "192.168.2.103"]
    '''
    range_list = ranges.split(',')
    ip_obj_list = []
    for _range in ranges.split(','):
        ip_obj_list += list(iter_iprange(*_range.split('-')))
    ip_list = [str(ip) for ip in ip_obj_list]
    if len(ip_list) < needed:
        raise ValueError('There is not enough IP addresses in ranges: "{}". {} available, {} required.'.format(ranges, len(ip_list), needed))
    return ip_list
