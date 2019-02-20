import datetime
import logging
import pykube

from collections import Counter

from .helper import parse_ttl, format_duration
from .resources import get_namespaced_resource_types
from pykube import Namespace, Event

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


def create_event(resource, message: str, dry_run: bool):
    now = datetime.datetime.utcnow()
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    event = Event(resource.api, {
        'metadata': {'namespace': resource.namespace, 'generateName': 'kube-janitor-'},
        'type': 'Normal',
        'count': 1,
        'firstTimestamp': timestamp,
        'lastTimestamp': timestamp,
        'reason': 'TimeToLiveExpired',
        'involvedObject': {
            'apiVersion': resource.version,
            'name': resource.name,
            'namespace': resource.namespace,
            'kind': resource.kind,
            'resourceVersion': resource.metadata.get('resourceVersion'),
            # https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#uids
            'uid': resource.metadata.get('uid')
        },
        'message': message,
        'source': {
            'component': 'kube-janitor'
        }

    })
    if not dry_run:
        try:
            event.create()
        except Exception as e:
            logger.error(f'Could not create event {event.obj}: {e}')


def delete(resource, dry_run: bool):
    if dry_run:
        logger.info(f'**DRY-RUN**: would delete {resource.kind} {resource.namespace}/{resource.name}')
    else:
        logger.info(f'Deleting {resource.kind} {resource.namespace}/{resource.name}..')
        try:
            resource.delete()
        except Exception as e:
            logger.error(f'Could not delete {resource.kind} {resource.namespace}/{resource.name}: {e}')


def handle_resource(resource, rules, dry_run: bool):
    counter = {'resources-processed': 1}

    ttl = resource.annotations.get(TTL_ANNOTATION)
    if ttl:
        reason = f'annotation {TTL_ANNOTATION} is set'
    else:
        for rule in rules:
            if rule.matches(resource):
                logger.debug(f'Rule {rule.id} applies {rule.ttl} TTL to {resource.kind} {resource.namespace}/{resource.name}')
                ttl = rule.ttl
                reason = f'rule {rule.id} matches'
                counter[f'rule-{rule.id}-matches'] = 1
                # first rule which matches
                break
    if ttl:
        try:
            ttl_seconds = parse_ttl(ttl)
        except ValueError as e:
            logger.info(f'Ignoring invalid TTL on {resource.kind} {resource.name}: {e}')
        else:
            counter[f'{resource.endpoint}-with-ttl'] = 1
            age = get_age(resource)
            age_formatted = format_duration(int(age.total_seconds()))
            logger.debug(f'{resource.kind} {resource.name} with {ttl} TTL is {age_formatted} old')
            if age.total_seconds() > ttl_seconds:
                message = f'{resource.kind} {resource.name} with {ttl} TTL is {age_formatted} old and will be deleted ({reason})'
                logger.info(message)
                create_event(resource, message, dry_run=dry_run)
                delete(resource, dry_run=dry_run)
                counter[f'{resource.endpoint}-deleted'] = 1

    return counter


def clean_up(api,
             include_resources: frozenset,
             exclude_resources: frozenset,
             include_namespaces: frozenset,
             exclude_namespaces: frozenset,
             rules: list,
             dry_run: bool):

    counter = Counter()

    for namespace in Namespace.objects(api):
        if matches_resource_filter(namespace, include_resources, exclude_resources, include_namespaces, exclude_namespaces):
            counter.update(handle_resource(namespace, rules, dry_run))
        else:
            logger.debug(f'Skipping {namespace.kind} {namespace}')

    already_seen = set()

    filtered_resources = []

    resource_types = get_namespaced_resource_types(api)
    for _type in resource_types:
        if _type.endpoint not in exclude_resources:
            try:
                for resource in _type.objects(api, namespace=pykube.all):
                    # objects might be available via multiple API versions (e.g. deployments appear as extensions/v1beta1 and apps/v1)
                    # => process them only once
                    object_id = (resource.kind, resource.namespace, resource.name)
                    if object_id in already_seen:
                        continue
                    already_seen.add(object_id)
                    if matches_resource_filter(resource, include_resources, exclude_resources, include_namespaces, exclude_namespaces):
                        filtered_resources.append(resource)
                    else:
                        logger.debug(f'Skipping {resource.kind} {resource.namespace}/{resource.name}')
            except Exception as e:
                logger.error(f'Could not list {_type.kind} objects: {e}')

    for resource in filtered_resources:
        counter.update(handle_resource(resource, rules, dry_run))

    stats = ', '.join([f'{k}={v}' for k, v in counter.items()])
    logger.info(f'Clean up run completed: {stats}')
    return counter
