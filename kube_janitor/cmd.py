import os

import argparse

DEFAULT_EXCLUDE_RESOURCES = "events,controllerrevisions"
DEFAULT_EXCLUDE_NAMESPACES = "kube-system"


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        help="Dry run mode: do not change anything, just print what would be done",
        action="store_true",
    )
    parser.add_argument(
        "--debug", "-d", help="Debug mode: print more information", action="store_true"
    )
    parser.add_argument(
        "--once", help="Run loop only once and exit", action="store_true"
    )
    parser.add_argument(
        "--interval", type=int, help="Loop interval (default: 30s)", default=30
    )
    parser.add_argument(
        "--delete-notification",
        type=int,
        help="Send an event seconds before to warn of the deletion",
        required=False,
    )
    parser.add_argument(
        "--include-resources",
        help="Resources to consider for clean up (default: all)",
        default=os.getenv("INCLUDE_RESOURCES", "all"),
    )
    parser.add_argument(
        "--exclude-resources",
        help=f"Resources to exclude from clean up (default: {DEFAULT_EXCLUDE_RESOURCES})",
        default=os.getenv("EXCLUDE_RESOURCES", DEFAULT_EXCLUDE_RESOURCES),
    )
    parser.add_argument(
        "--include-namespaces",
        help="Include namespaces for clean up (default: all)",
        default=os.getenv("INCLUDE_NAMESPACES", "all"),
    )
    parser.add_argument(
        "--exclude-namespaces",
        help=f"Exclude namespaces from clean up (default: {DEFAULT_EXCLUDE_NAMESPACES})",
        default=os.getenv("EXCLUDE_NAMESPACES", DEFAULT_EXCLUDE_NAMESPACES),
    )
    parser.add_argument(
        "--rules-file",
        help="Load TTL rules from given file path",
        default=os.getenv("RULES_FILE"),
    )
    return parser
