import kube_janitor.example_hooks
from kube_janitor.cmd import get_hook_function
from kube_janitor.cmd import get_parser


def test_parse_args():
    parser = get_parser()
    parser.parse_args(["--dry-run", "--rules-file=/config/rules.yaml"])


def test_get_example_hook_function():
    func = get_hook_function("kube_janitor.example_hooks.random_dice")
    assert func == kube_janitor.example_hooks.random_dice
