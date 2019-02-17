from unittest.mock import MagicMock

from pykube.objects import NamespacedAPIObject
from pykube import Namespace
from kube_janitor.janitor import matches_resource_filter, clean_up

ALL = frozenset(['all'])


def test_matches_resource_filter():
    foo_ns = Namespace(None, {'metadata': {'name': 'foo'}})
    assert not matches_resource_filter(foo_ns, [], [], [], [])
    assert not matches_resource_filter(foo_ns, ALL, [], [], [])
    assert matches_resource_filter(foo_ns, ALL, [], ALL, [])
    assert not matches_resource_filter(foo_ns, ALL, [], ALL, ['foo'])
    assert not matches_resource_filter(foo_ns, ALL, ['namespaces'], ALL, [])
    assert matches_resource_filter(foo_ns, ALL, ['deployments'], ALL, ['kube-system'])


def test_clean_up_default():
    api_mock = MagicMock(spec=NamespacedAPIObject, name='APIMock')

    def get(**kwargs):
        if kwargs.get('url') == 'namespaces':
            data = {'items': [{'metadata': {'name': 'default'}}]}
        elif kwargs['version'] == 'v1':
            data = {'resources': []}
        elif kwargs['version'] == '/apis':
            data = {'groups': []}
        else:
            data = {}
        response = MagicMock()
        response.json.return_value = data
        return response
    api_mock.get = get
    clean_up(api_mock, ALL, [], ALL, ['kube-system'], dry_run=False)


def test_clean_up_custom_resource():
    api_mock = MagicMock(spec=NamespacedAPIObject, name='APIMock')

    def get(**kwargs):
        if kwargs.get('url') == 'namespaces':
            data = {'items': [{'metadata': {'name': 'ns-1'}}]}
        if kwargs.get('url') == 'customfoos':
            data = {'items': [{'metadata': {
                'name': 'foo-1',
                'namespace': 'ns-1',
                'creationTimestamp': '2019-01-17T15:14:38Z',
                'annotations': {'janitor/ttl': '10m'}}}]}
        elif kwargs['version'] == 'v1':
            data = {'resources': []}
        elif kwargs['version'] == 'srcco.de/v1':
            data = {'resources': [{'kind': 'CustomFoo', 'name': 'customfoos', 'namespaced': True, 'verbs': ['delete']}]}
        elif kwargs['version'] == '/apis':
            data = {'groups': [{'preferredVersion': {'groupVersion': 'srcco.de/v1'}}]}
        else:
            data = {}
        response = MagicMock()
        response.json.return_value = data
        return response

    api_mock.get = get
    clean_up(api_mock, ALL, [], ALL, [], dry_run=False)

    # verify that the delete call happened
    api_mock.delete.assert_called_once_with(namespace='ns-1', url='customfoos/foo-1', version='srcco.de/v1')
