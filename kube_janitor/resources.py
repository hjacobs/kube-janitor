import logging

from pykube.objects import NamespacedAPIObject

logger = logging.getLogger(__name__)


def namespaced_object_factory(kind: str, name: str, api_version: str):
    # https://github.com/kelproject/pykube/blob/master/pykube/objects.py#L138
    return type(
        kind,
        (NamespacedAPIObject,),
        {"version": api_version, "endpoint": name, "kind": kind},
    )


def discover_namespaced_api_resources(api):
    core_version = "v1"
    r = api.get(version=core_version)
    r.raise_for_status()
    for resource in r.json()["resources"]:
        # ignore subresources like pods/proxy
        if (
            resource["namespaced"]
            and "delete" in resource["verbs"]
            and "/" not in resource["name"]
        ):
            yield core_version, resource

    r = api.get(version="/apis")
    r.raise_for_status()
    for group in r.json()["groups"]:
        try:
            pref_version = group["preferredVersion"]["groupVersion"]
            logger.debug(f"Collecting resources in API group {pref_version}..")
            r2 = api.get(version=pref_version)
            r2.raise_for_status()
            for resource in r2.json()["resources"]:
                if (
                    resource["namespaced"]
                    and "delete" in resource["verbs"]
                    and "/" not in resource["name"]
                ):
                    yield pref_version, resource
        except Exception as e:
            logger.error(
                f"Could not collect resources in API group {pref_version}: {e}"
            )


def get_namespaced_resource_types(api):
    for api_version, resource in discover_namespaced_api_resources(api):
        clazz = namespaced_object_factory(
            resource["kind"], resource["name"], api_version
        )
        yield clazz
