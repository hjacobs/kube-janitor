import os

import pykube
import re

TIME_UNIT_TO_SECONDS = {
    's': 1,
    'm': 60,
    'h': 60*60,
    'd': 60*60*24,
    'w': 60*60*24*7
}

FACTOR_TO_TIME_UNIT = list(sorted([(v, k) for k, v in TIME_UNIT_TO_SECONDS.items()], reverse=True))

TTL_PATTERN = re.compile(r'^(\d+)([smhdw])$')


def parse_ttl(ttl: str) -> int:
    match = TTL_PATTERN.match(ttl)
    if not match:
        raise ValueError(
            f'TTL value "{ttl}" does not match format (e.g. 60s, 5m, 8h, 7d, 2w)')

    value = int(match.group(1))
    unit = match.group(2)

    multiplier = TIME_UNIT_TO_SECONDS.get(unit)

    if not multiplier:
        raise ValueError(f'Unknown time unit "{unit}" for TTL "{ttl}"')

    return value * multiplier


def format_duration(seconds: int) -> str:
    '''
    Print a given duration in seconds (positive integer) as human readable duration string

    >>> format_duration(3900)
    1h5m
    '''

    parts = []
    if seconds < 0:
        # special handling for negative durations
        # use positive (absolute value) with divmod, but add negative sign
        parts.append('-')
    remainder = abs(seconds)
    for factor, unit in FACTOR_TO_TIME_UNIT:
        value, remainder = divmod(remainder, factor)
        if value > 0 or (seconds == 0 and factor == 1):
            parts.append(f'{value}{unit}')
    return ''.join(parts)


def get_kube_api():
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        # local testing
        config = pykube.KubeConfig.from_file(os.getenv('KUBECONFIG', os.path.expanduser('~/.kube/config')))
    api = pykube.HTTPClient(config)
    return api
