import os

import argparse


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', help='Dry run mode: do not change anything, just print what would be done',
                        action='store_true')
    parser.add_argument('--debug', '-d', help='Debug mode: print more information', action='store_true')
    parser.add_argument('--once', help='Run loop only once and exit', action='store_true')
    parser.add_argument('--interval', type=int, help='Loop interval (default: 30s)', default=30)
    parser.add_argument('--include-resources', help='Resources to consider for clean up (default: all)',
                        default=os.getenv('INCLUDE_RESOURCES', 'all'))
    parser.add_argument('--exclude-resources', help='Resources to exclude from clean up (default: none)',
                        default=os.getenv('EXCLUDE_RESOURCES', ''))
    parser.add_argument('--include-namespaces', help='Include namespaces for clean up (default: all)',
                        default=os.getenv('INCLUDE_NAMESPACES', 'all'))
    parser.add_argument('--exclude-namespaces', help='Exclude namespaces from clean up (default: kube-system)',
                        default=os.getenv('EXCLUDE_NAMESPACES', 'kube-system'))
    return parser
