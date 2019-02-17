from unittest.mock import MagicMock

from pykube.objects import NamespacedAPIObject
from pykube import Namespace
from kube_janitor.janitor import matches_resource_filter, clean_up


def test_matches_resource_filter():
    foo_ns = Namespace(None, {'metadata': {'name': 'foo'}})
    assert not matches_resource_filter(foo_ns, [], [], [], [])
    assert not matches_resource_filter(foo_ns, ['all'], [], [], [])
    assert matches_resource_filter(foo_ns, ['all'], [], ['all'], [])
    assert not matches_resource_filter(foo_ns, ['all'], [], ['all'], ['foo'])
    assert not matches_resource_filter(foo_ns, ['all'], ['namespaces'], ['all'], [])
    assert matches_resource_filter(foo_ns, ['all'], ['deployments'], ['all'], ['kube-system'])


def test_clean_up_default():
    api_mock = MagicMock(spec=NamespacedAPIObject, name='APIMock')

    def get(**kwargs):
        response = MagicMock()
        response.json.return_value = {'items': [{'metadata': {'name': 'default'}}]}
        return response
    api_mock.get = get
    clean_up(api_mock, ['all'], [], ['all'], ['kube-system'], dry_run=False)
