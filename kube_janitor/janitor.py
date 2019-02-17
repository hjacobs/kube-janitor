import datetime
import logging

from .helper import parse_ttl
from pykube import Namespace

logger = logging.getLogger(__name__)
TTL_ANNOTATION = 'janitor/ttl'


def matches_resource_filter(resource, include_resources: frozenset, exclude_resources: frozenset,
                            include_namespaces: frozenset, exclude_namespaces: frozenset):

    resource_type_plural = resource.endpoint
    if resource.kind == 'Namespace':
        namespace = resource.name
    else:
        namespace = resource.namespace

    if namespace is None:
        # skip all non-namespaced resources
        return False

    resource_included = 'all' in include_resources or resource_type_plural in include_resources
    namespace_included = 'all' in include_namespaces or namespace in include_namespaces
    resource_excluded = resource_type_plural in exclude_resources
    namespace_excluded = namespace in exclude_namespaces
    return resource_included and not resource_excluded and namespace_included and not namespace_excluded


def get_age(resource):
    creation_time = datetime.datetime.strptime(resource.metadata['creationTimestamp'], '%Y-%m-%dT%H:%M:%SZ')
    now = datetime.datetime.utcnow()
    age = now - creation_time
    return age


def delete(resource, dry_run: bool):
    if dry_run:
        logger.info(f'**DRY-RUN**: would delete {resource.kind} {resource.namespace}/{resource.name}')
    else:
        logger.info(f'Deleting {resource.kind} {resource.namespace}/{resource.name}..')
        try:
            resource.delete()
        except Exception as e:
            logger.error(f'Could not delete {resource.kind} {resource.namespace}/{resource.name}: {e}')


def clean_up(api,
             include_resources: frozenset,
             exclude_resources: frozenset,
             include_namespaces: frozenset,
             exclude_namespaces: frozenset,
             dry_run: bool):
    for namespace in Namespace.objects(api):
        if not matches_resource_filter(namespace, include_resources, exclude_resources, include_namespaces, exclude_namespaces):
            logger.debug(f'Skipping namespace {namespace}')
            continue
        ttl = namespace.annotations.get(TTL_ANNOTATION)
        if ttl:
            try:
                ttl_seconds = parse_ttl(ttl)
            except ValueError as e:
                logger.info(f'Ignoring invalid TTL on namespace {namespace}: {e}')
            else:
                age = get_age(namespace)
                logger.debug(f'Namespace {namespace} has TTL of {ttl} is {age} old')
                if age.total_seconds() > ttl_seconds:
                    logger.info(f'Namespace {namespace} with TTL of {ttl} is {age} old and will be deleted')
                    delete(namespace, dry_run=dry_run)
