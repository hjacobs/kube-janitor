from unittest.mock import MagicMock

import yaml
from pykube.objects import Namespace
from pykube.objects import PersistentVolumeClaim

import kube_janitor.example_hooks
from kube_janitor.resource_context import get_resource_context

JOB_WITH_VOLUME = """
apiVersion: batch/v1
kind: Job
metadata:
  name: pi
spec:
  template:
    spec:
      containers:
      - name: pi
        image: my-image
        volumeMounts:
          - mountPath: "/data"
            name: "job-data"
      volumes:
        - name: "foobar-data"
          persistentVolumeClaim:
            claimName: "job-data"
"""

CRONJOB_WITH_VOLUME = """
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: "foobar"
spec:
  schedule: "0 23 * * *"
  concurrencyPolicy: Forbid
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            application: "foobar"
        spec:
          restartPolicy: Never
          containers:
            - name: cont
              image: "my-docker-image"
              volumeMounts:
                - mountPath: "/data"
                  name: "foobar-data"
          volumes:
            - name: "foobar-data"
              persistentVolumeClaim:
                claimName: "foobar-data"
"""

# this example is not good practice (Redis as "Deployment"),
# but people use it in the wild ;-)
DEPLOYMENT_WITH_VOLUME = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  template:
    metadata:
      labels:
        application: redis-myteam
        version: 3.2.5
    spec:
      containers:
      - name: redis
        image: redis:3.2.5
        volumeMounts:
        - mountPath: /data
          name: redis-data
      volumes:
        - name: redis-data
          persistentVolumeClaim:
            claimName: redis-data
"""


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


def test_pvc_is_referenced_by_statefulset():
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


def test_pvc_is_referenced_by_cronjob():
    api_mock = MagicMock(name="APIMock")

    def get(**kwargs):
        if kwargs.get("url") == "cronjobs":
            data = {"items": [yaml.safe_load(CRONJOB_WITH_VOLUME)]}
        else:
            data = {}
        response = MagicMock()
        response.json.return_value = data
        return response

    api_mock.get = get

    pvc = PersistentVolumeClaim(api_mock, {"metadata": {"name": "foobar-data"}})

    context = get_resource_context(pvc)
    assert not context["pvc_is_not_referenced"]


def test_pvc_is_referenced_by_job():
    api_mock = MagicMock(name="APIMock")

    def get(**kwargs):
        if kwargs.get("url") == "jobs":
            data = {"items": [yaml.safe_load(JOB_WITH_VOLUME)]}
        else:
            data = {}
        response = MagicMock()
        response.json.return_value = data
        return response

    api_mock.get = get

    pvc = PersistentVolumeClaim(api_mock, {"metadata": {"name": "job-data"}})

    context = get_resource_context(pvc)
    assert not context["pvc_is_not_referenced"]


def test_pvc_is_referenced_by_deployment():
    api_mock = MagicMock(name="APIMock")

    def get(**kwargs):
        if kwargs.get("url") == "deployments":
            data = {"items": [yaml.safe_load(DEPLOYMENT_WITH_VOLUME)]}
        else:
            data = {}
        response = MagicMock()
        response.json.return_value = data
        return response

    api_mock.get = get

    pvc = PersistentVolumeClaim(api_mock, {"metadata": {"name": "redis-data"}})

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
