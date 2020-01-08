import pytest
from pykube.objects import Deployment
from pykube.objects import StatefulSet

from kube_janitor.rules import load_rules_from_file
from kube_janitor.rules import Rule


def test_load_rules_from_wrong_file(tmpdir):
    p = tmpdir.join("wrong.yaml")
    p.write("wrongformat")
    with pytest.raises(KeyError):
        load_rules_from_file(str(p))


def test_load_rules_from_empty_file(tmpdir):
    p = tmpdir.join("empty.yaml")
    p.write("rules: []")
    load_rules_from_file(str(p))


def test_load_rules_from_file_no_mapping(tmpdir):
    p = tmpdir.join("missing-keys.yaml")
    p.write(
        """rules:
                 - foo
                 - bar
            """
    )
    with pytest.raises(TypeError):
        load_rules_from_file(str(p))


def test_load_rules_from_file_missing_keys(tmpdir):
    p = tmpdir.join("missing-keys.yaml")
    p.write(
        """rules:
                 - resources: [foos, bars]
                   jmespath: a.b.c
                   ttl: 5m
            """
    )
    with pytest.raises(TypeError):
        load_rules_from_file(str(p))


def test_load_rules_from_file(tmpdir):
    p = tmpdir.join("rules.yaml")
    p.write(
        """rules:
                 - id: rule-1
                   resources: [foos, bars]
                   jmespath: a.b.c
                   ttl: 5m
            """
    )
    load_rules_from_file(str(p))


def test_rule_invalid_id():
    with pytest.raises(ValueError):
        Rule.from_entry({"id": "X", "resources": [], "jmespath": "a.b", "ttl": "1s"})


def test_rule_matches():
    rule = Rule.from_entry(
        {
            "id": "test",
            "resources": ["deployments"],
            "jmespath": "metadata.labels.app",
            "ttl": "30m",
        }
    )
    resource = Deployment(None, {"metadata": {"namespace": "ns-1", "name": "deploy-1"}})
    assert not rule.matches(resource)
    resource.obj["metadata"]["labels"] = {"app": ""}
    assert not rule.matches(resource)
    resource.obj["metadata"]["labels"]["app"] = "foobar"
    assert rule.matches(resource)

    resource = StatefulSet(None, {"metadata": {"namespace": "ns-1", "name": "ss-1"}})
    assert not rule.matches(resource)

    resource = StatefulSet(
        None,
        {"metadata": {"namespace": "ns-1", "name": "ss-1", "labels": {"app": "x"}}},
    )
    assert not rule.matches(resource)
