from itertools import chain
from netaddr import iter_iprange, IPAddress, IPNetwork

__virtualname__ = 'netutils'


def __virtual__():
    return __virtualname__


def parse_ip_ranges(ranges, needed):
    '''
    Takes comma seprated list of IP ranges and returns full list of IP addresses in these ranges.
    Second argument is used to check if there is enough IP addresses to cover the required number of nodes.

    >>> parse_ip_ranges("192.168.1.101-192.168.1.103,192.168.2.101-192.168.2.103")
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


def parse_network_ranges(ranges, iterate=False):
    '''
    Takes comma separated list of network ranges and returns full list of first IP addresses in every given subnet.
    Second argument is used to check if there is enough IP addresses to cover the required number of nodes.

    >>> parse_network_ranges("10.10.0.1/24-10.10.10.1/24,192.168.0.1/24-192.168.10.1/24")
    ['10.10.0.1', '10.10.1.1', '10.10.2.1', '10.10.3.1', '10.10.4.1', '10.10.5.1', '10.10.6.1', '10.10.7.1', '10.10.8.1', '10.10.9.1', '10.10.10.1', '192.168.0.1', '192.168.1.1', '192.168.2.1', '192.168.3.1', '192.168.4.1', '192.168.5.1', '192.168.6.1', '192.168.7.1', '192.168.8.1', '192.168.9.1', '192.168.10.1']
    '''
    def _iter_subnet_list(start, end):
        yield str(IPAddress(start.first) + 1)
        if start != end:
            for ip in _iter_subnet_list(start.next(), end):
                yield ip

    generators = tuple()

    for _range in ranges.split(','):
        start_str, end_str = _range.split('-')
        start, end = IPNetwork(start_str), IPNetwork(end_str)
        if start > end:
            raise ValueError('Invalid network range, start address is higher than end address')
        generators += (_iter_subnet_list(start, end),)

    if iterate:
        return [ip for ip in chain(*generators)]
    return chain(*generators)
