import logging
import re
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

import jmespath
from pykube import HTTPClient
from pykube.objects import APIObject
from pykube.objects import CronJob
from pykube.objects import Deployment
from pykube.objects import Job
from pykube.objects import NamespacedAPIObject
from pykube.objects import Pod
from pykube.objects import StatefulSet

logger = logging.getLogger(__name__)

PVC_REFERENCES = {
    Pod: jmespath.compile("spec.volumes[].persistentVolumeClaim"),
    Job: jmespath.compile("spec.template.spec.volumes[].persistentVolumeClaim"),
    Deployment: jmespath.compile("spec.template.spec.volumes[].persistentVolumeClaim"),
    CronJob: jmespath.compile(
        "spec.jobTemplate.spec.template.spec.volumes[].persistentVolumeClaim"
    ),
}


def get_objects_in_namespace(
    clazz, api: HTTPClient, namespace: str, cache: Dict[str, Any]
):
    """Get (cached) objects from the Kubernetes API."""
    cache_key = f"{namespace}/{clazz.endpoint}"
    objects = cache.get(cache_key)
    if objects is None:
        objects = list(clazz.objects(api, namespace=namespace))
        cache[cache_key] = objects

    return objects


def is_pvc_referenced_by_object(
    pvc: NamespacedAPIObject, obj: NamespacedAPIObject, claim_path
) -> bool:
    """Check whether the given PVC is referenced by `obj` using the passed JMESpath to find volume claims."""
    for claim in claim_path.search(obj.obj) or []:
        if claim.get("claimName") == pvc.name:
            return True
    return False


def get_persistent_volume_claim_context(
    pvc: NamespacedAPIObject, cache: Dict[str, Any]
) -> Dict[str, Any]:
    """Get context for PersistentVolumeClaim: whether it's mounted by a Pod and whether it's referenced by a StatefulSet."""
    pvc_is_mounted = False
    pvc_is_referenced = False

    for clazz, claim_path in PVC_REFERENCES.items():
        if pvc_is_referenced:
            break
        # find out whether the PVC is still mounted by a Pod or referenced by some object
        for obj in get_objects_in_namespace(clazz, pvc.api, pvc.namespace, cache):
            if is_pvc_referenced_by_object(pvc, obj, claim_path):
                if clazz is Pod:
                    verb = "mounted"
                    pvc_is_mounted = True
                else:
                    verb = "referenced"
                logger.debug(
                    f"{pvc.kind} {pvc.namespace}/{pvc.name} is {verb} by {obj.kind} {obj.name}"
                )
                pvc_is_referenced = True
                break

    if not pvc_is_referenced:
        # find out whether the PVC is still referenced by a StatefulSet
        for sts in get_objects_in_namespace(StatefulSet, pvc.api, pvc.namespace, cache):
            # see https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
            for claim_template in sts.obj.get("spec", {}).get(
                "volumeClaimTemplates", []
            ):
                claim_prefix = claim_template.get("metadata", {}).get("name")
                claim_name_pattern = re.compile(f"^{claim_prefix}-{sts.name}-[0-9]+$")
                if claim_name_pattern.match(pvc.name):
                    logger.debug(
                        f"{pvc.kind} {pvc.namespace}/{pvc.name} is referenced by {sts.kind} {sts.name}"
                    )
                    pvc_is_referenced = True
                    break

    # negate the property to make it less error-prone for JMESpath usage
    return {
        "pvc_is_not_mounted": not pvc_is_mounted,
        "pvc_is_not_referenced": not pvc_is_referenced,
    }


def get_resource_context(
    resource: APIObject,
    hook: Optional[Callable[[APIObject, dict], Dict[str, Any]]] = None,
    cache: Optional[Dict[str, Any]] = None,
):
    """Get additional context information for a single resource, e.g. whether a PVC is mounted/used or not."""

    context: Dict[str, Any] = {}

    if cache is None:
        cache = {}

    if resource.kind == "PersistentVolumeClaim":
        context.update(get_persistent_volume_claim_context(resource, cache))

    if hook:
        try:
            context.update(hook(resource, cache))
        except Exception as e:
            logger.exception(
                f"Failed populating _context from resource context hook: {e}"
            )

    return context
