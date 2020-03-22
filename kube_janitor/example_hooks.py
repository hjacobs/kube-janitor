"""
Example resource context hooks for Kubernetes Janitor.

Usage: --resource-context-hook=kube_janitor.example_hooks.random_dice
"""
import logging
import random
from typing import Any
from typing import Dict

from pykube.objects import APIObject

logger = logging.getLogger(__name__)

CACHE_KEY = "random_dice"


def random_dice(resource: APIObject, cache: Dict[str, Any]) -> Dict[str, Any]:
    """Built-in example resource context hook to set ``_context.random_dice`` to a random dice value (1-6)."""

    # re-use any value from the cache to have only one dice roll per janitor run
    dice_value = cache.get(CACHE_KEY)

    if dice_value is None:
        # roll the dice
        dice_value = random.randint(1, 6)
        logger.debug(f"The random dice value is {dice_value}!")
        cache[CACHE_KEY] = dice_value

    return {"random_dice": dice_value}
