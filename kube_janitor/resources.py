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


def discover_api_group(api, group_version: str):
    logger.debug(f"Collecting resources in API group {group_version}..")
    response = api.get(version=group_version)
    response.raise_for_status()
    return response.json()["resources"]


def discover_namespaced_api_resources(api):
    core_version = "v1"
    r = api.get(version=core_version)
    r.raise_for_status()
    for resource in r.json()["resources"]:
        # ignore subresources like pods/proxy
        if (
            resource["namespaced"]
            and "/" not in resource["name"]
            and "delete" in resource["verbs"]
        ):
            yield core_version, resource

    r = api.get(version="/apis")
    r.raise_for_status()
    group_versions = set()
    for group in r.json()["groups"]:
        pref_version = group["preferredVersion"]["groupVersion"]
        group_versions.add((pref_version, pref_version))
        for version in group.get("versions", []):
            group_version = version["groupVersion"]
            group_versions.add((group_version, pref_version))

    yielded = set()
    non_preferred = []
    for group_version, pref_version in sorted(group_versions):
        try:
            resources = discover_api_group(api, group_version)
        except Exception as e:
            # do not crash if one API group is not available
            # see https://codeberg.org/hjacobs/kube-web-view/issues/64
            logger.warning(
                f"Could not collect resources in API group {group_version}: {e}"
            )
            continue

        for resource in resources:
            if (
                resource["namespaced"]
                and "/" not in resource["name"]
                and "delete" in resource["verbs"]
            ):
                if group_version == pref_version:
                    yield group_version, resource
                    yielded.add((group_version, resource["name"]))
                else:
                    non_preferred.append((group_version, resource))

    for group_version, resource in non_preferred:
        if (group_version, resource["name"]) not in yielded:
            yield group_version, resource


def get_namespaced_resource_types(api):
    for api_version, resource in discover_namespaced_api_resources(api):
        clazz = namespaced_object_factory(
            resource["kind"], resource["name"], api_version
        )
        yield clazz
