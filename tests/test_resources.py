from unittest.mock import MagicMock

from kube_janitor.resources import get_namespaced_resource_types


def test_get_namespaced_resource_types():
    api_mock = MagicMock()

    def api_get(version):
        if version == "v1":
            # shortened dump from a real cluster (/api/v1/)
            data = {
                "groupVersion": "v1",
                "kind": "APIResourceList",
                "resources": [
                    {
                        "kind": "Namespace",
                        "name": "namespaces",
                        "namespaced": False,
                        "shortNames": ["ns"],
                        "singularName": "",
                        "storageVersionHash": "Q3oi5N2YM8M=",
                        "verbs": [
                            "create",
                            "delete",
                            "get",
                            "list",
                            "patch",
                            "update",
                            "watch",
                        ],
                    },
                    {
                        "kind": "Namespace",
                        "name": "namespaces/finalize",
                        "namespaced": False,
                        "singularName": "",
                        "verbs": ["update"],
                    },
                ],
            }
        elif version == "/apis":
            # shortened dump from a real cluster (/apis/)
            data = {
                "kind": "APIGroupList",
                "apiVersion": "v1",
                "groups": [
                    {
                        "name": "zalando.org",
                        "versions": [
                            {"groupVersion": "zalando.org/v1", "version": "v1"},
                            {
                                "groupVersion": "zalando.org/v1alpha1",
                                "version": "v1alpha1",
                            },
                        ],
                        "preferredVersion": {
                            "groupVersion": "zalando.org/v1",
                            "version": "v1",
                        },
                    }
                ],
            }
        elif version == "zalando.org/v1":
            data = {
                "kind": "APIResourceList",
                "apiVersion": "v1",
                "groupVersion": "zalando.org/v1",
                "resources": [
                    # StackSet CRD
                    # see https://github.com/zalando-incubator/stackset-controller
                    {
                        "name": "stacksets",
                        "singularName": "stackset",
                        "namespaced": True,
                        "kind": "StackSet",
                        "verbs": [
                            "delete",
                            "deletecollection",
                            "get",
                            "list",
                            "patch",
                            "create",
                            "update",
                            "watch",
                        ],
                        "categories": ["all"],
                        "storageVersionHash": "G0lLCsF1uVM=",
                    }
                ],
            }
        elif version == "zalando.org/v1alpha1":
            data = {
                "kind": "APIResourceList",
                "apiVersion": "v1",
                "groupVersion": "zalando.org/v1alpha1",
                "resources": [
                    {
                        "name": "fabriceventstreams",
                        "singularName": "fabriceventstream",
                        "namespaced": True,
                        "kind": "FabricEventStream",
                        "verbs": [
                            "delete",
                            "deletecollection",
                            "get",
                            "list",
                            "patch",
                            "create",
                            "update",
                            "watch",
                        ],
                        "shortNames": ["fes"],
                        "storageVersionHash": "K2/8aDi0wOY=",
                    }
                ],
            }

        response = MagicMock()
        response.json.return_value = data
        return response

    api_mock.get = api_get

    resource_types = list(get_namespaced_resource_types(api_mock))
    kinds = set(f"{clazz.kind} ({clazz.version})" for clazz in resource_types)
    assert kinds == frozenset(
        ["StackSet (zalando.org/v1)", "FabricEventStream (zalando.org/v1alpha1)"]
    )
