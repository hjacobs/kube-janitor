from unittest.mock import MagicMock

from pykube.objects import NamespacedAPIObject
from pykube import Namespace
from kube_janitor.janitor import matches_resource_filter, handle_resource, clean_up
from kube_janitor.rules import Rule

ALL = frozenset(['all'])


def test_matches_resource_filter():
    foo_ns = Namespace(None, {'metadata': {'name': 'foo'}})
    assert not matches_resource_filter(foo_ns, [], [], [], [])
    assert not matches_resource_filter(foo_ns, ALL, [], [], [])
    assert matches_resource_filter(foo_ns, ALL, [], ALL, [])
    assert not matches_resource_filter(foo_ns, ALL, [], ALL, ['foo'])
    assert not matches_resource_filter(foo_ns, ALL, ['namespaces'], ALL, [])
    assert matches_resource_filter(foo_ns, ALL, ['deployments'], ALL, ['kube-system'])


def test_handle_resource_no_ttl():
    resource = Namespace(None, {'metadata': {'name': 'foo'}})
    counter = handle_resource(resource, [], dry_run=True)
    assert counter == {'resources-processed': 1}


def test_handle_resource_ttl_annotation():
    # TTL is far in the future
    resource = Namespace(None, {'metadata': {'name': 'foo', 'annotations': {'janitor/ttl': '999w'}, 'creationTimestamp': '2019-01-17T20:59:12Z'}})
    counter = handle_resource(resource, [], dry_run=True)
    assert counter == {'resources-processed': 1, 'namespaces-with-ttl': 1}


def test_handle_resource_ttl_expired():
    resource = Namespace(None, {'metadata': {'name': 'foo', 'annotations': {'janitor/ttl': '1s'}, 'creationTimestamp': '2019-01-17T20:59:12Z'}})
    counter = handle_resource(resource, [], dry_run=True)
    assert counter == {'resources-processed': 1, 'namespaces-with-ttl': 1, 'namespaces-deleted': 1}


def test_clean_up_default():
    api_mock = MagicMock(spec=NamespacedAPIObject, name='APIMock')

    def get(**kwargs):
        if kwargs.get('url') == 'namespaces':
            # kube-system is skipped
            data = {'items': [{'metadata': {'name': 'default'}}, {'metadata': {'name': 'kube-system'}}]}
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
    counter = clean_up(api_mock, ALL, [], ALL, ['kube-system'], [], dry_run=False)

    assert counter['resources-processed'] == 1


def test_ignore_invalid_ttl():
    api_mock = MagicMock(spec=NamespacedAPIObject, name='APIMock')

    def get(**kwargs):
        if kwargs.get('url') == 'namespaces':
            data = {'items': [{'metadata': {'name': 'ns-1'}}]}
        elif kwargs.get('url') == 'customfoos':
            data = {'items': [{'metadata': {
                'name': 'foo-1',
                'namespace': 'ns-1',
                'creationTimestamp': '2019-01-17T15:14:38Z',
                # invalid TTL (no unit suffix)
                'annotations': {'janitor/ttl': '123'}}}]}
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
    counter = clean_up(api_mock, ALL, [], ALL, [], [], dry_run=False)

    # namespace ns-1 and object foo-1
    assert counter['resources-processed'] == 2
    assert counter['customfoos-with-ttl'] == 0
    assert counter['customfoos-deleted'] == 0

    assert not api_mock.delete.called


def test_clean_up_custom_resource():
    api_mock = MagicMock(spec=NamespacedAPIObject, name='APIMock')

    def get(**kwargs):
        if kwargs.get('url') == 'namespaces':
            data = {'items': [{'metadata': {'name': 'ns-1'}}]}
        elif kwargs.get('url') == 'customfoos':
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
    counter = clean_up(api_mock, ALL, [], ALL, [], [], dry_run=False)

    # namespace ns-1 and object foo-1
    assert counter['resources-processed'] == 2
    assert counter['customfoos-with-ttl'] == 1
    assert counter['customfoos-deleted'] == 1

    # verify that the delete call happened
    api_mock.delete.assert_called_once_with(namespace='ns-1', url='customfoos/foo-1', version='srcco.de/v1')


def test_clean_up_by_rule():
    api_mock = MagicMock(spec=NamespacedAPIObject, name='APIMock')

    rule = Rule.from_entry({'id': 'r1', 'resources': ['customfoos'], 'jmespath': "metadata.namespace == 'ns-1'", 'ttl': '10m'})

    def get(**kwargs):
        if kwargs.get('url') == 'namespaces':
            data = {'items': [{'metadata': {'name': 'ns-1'}}]}
        elif kwargs.get('url') == 'customfoos':
            data = {'items': [{'metadata': {
                'name': 'foo-1',
                'namespace': 'ns-1',
                'creationTimestamp': '2019-01-17T15:14:38Z',
                }}]}
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
    counter = clean_up(api_mock, ALL, [], ALL, [], [rule], dry_run=False)

    # namespace ns-1 and object foo-1
    assert counter['resources-processed'] == 2
    assert counter['rule-r1-matches'] == 1
    assert counter['customfoos-with-ttl'] == 1
    assert counter['customfoos-deleted'] == 1

    # verify that the delete call happened
    api_mock.delete.assert_called_once_with(namespace='ns-1', url='customfoos/foo-1', version='srcco.de/v1')
