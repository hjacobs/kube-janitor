from kube_janitor.cmd import get_parser


def test_parse_args():
    parser = get_parser()
    parser.parse_args(["--dry-run", "--rules-file=/config/rules.yaml"])
