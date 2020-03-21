import collections
import logging
import re

import jmespath
import yaml
from pykube.objects import NamespacedAPIObject

from .helper import parse_ttl

RULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")

logger = logging.getLogger(__name__)


class Rule(collections.namedtuple("Rule", ["id", "resources", "jmespath", "ttl"])):
    @staticmethod
    def from_entry(entry: dict):
        id_ = entry["id"]
        if not RULE_ID_PATTERN.match(id_):
            raise ValueError(
                f'Invalid rule ID "{id_}": it has to match ^[a-z][a-z0-9-]*$'
            )

        # check whether TTL format is correct
        parse_ttl(entry["ttl"])
        return Rule(
            id=id_,
            resources=frozenset(entry["resources"]),
            jmespath=jmespath.compile(entry["jmespath"]),
            ttl=entry["ttl"],
        )

    def matches(self, resource: NamespacedAPIObject, context: dict = None):
        if resource.endpoint not in self.resources and "*" not in self.resources:
            return False

        data = {"_context": context}
        data.update(resource.obj)
        result = self.jmespath.search(data)
        logger.debug(
            f'Rule {self.id} with JMESPath "{self.jmespath.expression}" evaluated for {resource.kind} {resource.namespace}/{resource.name}: {result}'
        )
        return bool(result)


def load_rules_from_file(filename: str):
    with open(filename) as fd:
        data = yaml.safe_load(fd)

    try:
        entries = data["rules"]
    except (TypeError, KeyError):
        raise KeyError(
            'The rules YAML file must have a top-level mapping with the key "rules"'
        )

    rules = []

    for i, entry in enumerate(entries):
        try:
            if not isinstance(entry, dict):
                raise TypeError("rule must be a mapping")

            missing_keys = frozenset(Rule._fields) - entry.keys()
            if missing_keys:
                raise ValueError(f"rule is missing required keys: {missing_keys}")

            rule = Rule.from_entry(entry)
            rules.append(rule)
        except Exception as e:
            raise TypeError(f'Failed to load rule #{i} from file "{filename}": {e}')

    return rules
