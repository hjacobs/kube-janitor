from unittest.mock import MagicMock

from pykube.objects import Namespace
from pykube.objects import PersistentVolumeClaim

import kube_janitor.example_hooks
from kube_janitor.resource_context import get_resource_context


def test_pvc_not_mounted():
    api_mock = MagicMock(name="APIMock")

    def get(**kwargs):
        if kwargs.get("url") == "pods":
            data = {"items": [{"metadata": {"name": "my-pod"}}]}
        else:
            data = {}
        response = MagicMock()
        response.json.return_value = data
        return response

    api_mock.get = get

    pvc = PersistentVolumeClaim(api_mock, {"metadata": {"name": "my-pvc"}})

    context = get_resource_context(pvc)
    assert context["pvc_is_not_mounted"]


def test_pvc_mounted():
    api_mock = MagicMock(name="APIMock")

    def get(**kwargs):
        if kwargs.get("url") == "pods":
            data = {
                "items": [
                    {
                        "metadata": {"name": "my-pod"},
                        "spec": {
                            "volumes": [
                                {"persistentVolumeClaim": {"claimName": "my-pvc"}}
                            ]
                        },
                    }
                ]
            }
        else:
            data = {}
        response = MagicMock()
        response.json.return_value = data
        return response

    api_mock.get = get

    pvc = PersistentVolumeClaim(api_mock, {"metadata": {"name": "my-pvc"}})

    context = get_resource_context(pvc)
    assert not context["pvc_is_not_mounted"]


def test_pvc_is_referenced():
    api_mock = MagicMock(name="APIMock")

    def get(**kwargs):
        if kwargs.get("url") == "statefulsets":
            data = {
                "items": [
                    {
                        "metadata": {"name": "my-sts"},
                        "spec": {
                            "volumeClaimTemplates": [{"metadata": {"name": "data"}}]
                        },
                    }
                ]
            }
        else:
            data = {}
        response = MagicMock()
        response.json.return_value = data
        return response

    api_mock.get = get

    pvc = PersistentVolumeClaim(api_mock, {"metadata": {"name": "data-my-sts-0"}})

    context = get_resource_context(pvc)
    assert not context["pvc_is_not_referenced"]


def test_example_hook():
    namespace = Namespace(None, {"metadata": {"name": "my-ns"}})
    hook = kube_janitor.example_hooks.random_dice
    cache = {}
    context = get_resource_context(namespace, hook, cache)
    value = context["random_dice"]
    assert 1 <= value <= 6

    # check that cache is used
    new_context = get_resource_context(namespace, hook, cache)
    assert new_context["random_dice"] == value
