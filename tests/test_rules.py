import pytest

from pykube.objects import Deployment

from kube_janitor.rules import Rule, load_rules_from_file


def test_load_rules_from_wrong_file(tmpdir):
    p = tmpdir.join("wrong.yaml")
    p.write("wrongformat")
    with pytest.raises(KeyError):
        load_rules_from_file(str(p))


def test_load_rules_from_empty_file(tmpdir):
    p = tmpdir.join("empty.yaml")
    p.write("rules: []")
    load_rules_from_file(str(p))


def test_rule_matches():
    rule = Rule.from_entry({'id': 'test', 'resources': ['deployments'], 'jmespath': 'metadata.labels.app', 'ttl': '30m'})
    resource = Deployment(None, {'metadata': {'namespace': 'ns-1', 'name': 'deploy-1'}})
    assert not rule.matches(resource)
    resource.obj['metadata']['labels'] = {'app': ''}
    assert not rule.matches(resource)
    resource.obj['metadata']['labels']['app'] = 'foobar'
    assert rule.matches(resource)
