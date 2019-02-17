==================
Kubernetes Janitor
==================

.. image:: https://travis-ci.org/hjacobs/kube-janitor.svg?branch=master
   :target: https://travis-ci.org/hjacobs/kube-janitor
   :alt: Travis CI Build Status

.. image:: https://coveralls.io/repos/github/hjacobs/kube-janitor/badge.svg?branch=master;_=1
   :target: https://coveralls.io/github/hjacobs/kube-janitor?branch=master
   :alt: Code Coverage

Kubernetes Janitor cleans up (deletes) Kubernetes resources after a configured TTL (time to live).
It processes all namespaces and all namespaced resources including custom resource definitions (CRDs) and will delete them
if the ``janitor/ttl`` annotation indicates the resource as expired.

Example use cases:

* Deploy the janitor to a test (non-prod) cluster and use namespaces with a TTL of 7 days (``janitor/ttl: 7d`` on the namespace object) for prototyping
* Annotate your temporary manual test nginx deployment with ``kubectl annotate deploy nginx janitor/ttl=24h`` to automatically delete it after 24 hours
* Automatically set ``janitor/ttl`` on resources created by your CI/CD pipeline for pull requests (so PR tests can run and resources are clean up later)


Usage
=====

Deploy the janitor into your cluster via (also works with Minikube):

.. code-block:: bash

    $ kubectl apply -f deploy/

The example configuration uses the ``--dry-run`` as a safety flag to prevent any deletion --- remove it to enable the janitor, e.g. by editing the deployment:

.. code-block:: bash

    $ kubectl edit deploy kube-janitor


Configuration
=============

The janitor is configured via command line args, environment variables and Kubernetes annotations.

Kubernetes annotations:

``janitor/ttl``
    Maximum time to live (TTL) for the annotated resource. Annotation value must be a string composed of a integer value and a unit suffix (``s``, ``m``, ``h``, ``d``), e.g. ``120s`` (120 seconds), ``5m`` (5 minutes), ``8h`` (8 hours), or ``7d`` (7 days).
    Note that the actual time of deletion depends on the Janitor's clean up interval. The resource will be deleted if its age (delta between now and the resource creation time) is greater than the specified TTL.

Available command line options:

``--dry-run``
    Dry run mode: do not change anything, just print what would be done
``--debug``
    Debug mode: print more information
``--once``
    Run only once and exit. This is useful if you run the Kubernetes Janitor as a ``CronJob``.
``--interval``
    Loop interval (default: 30s). This option only makes sense when the ``--once`` flag is not set.
``--include-resources``
    Include resources for clean up (default: all resources), can also be configured via environment variable ``INCLUDE_RESOURCES``. This option can be used if you want to clean up only certain resource types, e.g. only ``deployments``.
``--exclude-resources``
    Exclude resources from clean up (default: events,controllerrevisions), can also be configured via environment variable ``EXCLUDE_RESOURCES``.
``--include-namespaces``
    Include namespaces for clean up (default: all namespaces), can also be configured via environment variable ``INCLUDE_NAMESPACES``
``--exclude-namespaces``
    Exclude namespaces from clean up (default: kube-system), can also be configured via environment variable ``EXCLUDE_NAMESPACES``


Contributing
============

Easiest way to contribute is to provide feedback! We would love to hear what you like and what you think is missing.
Create an issue or `ping try_except_ on Twitter`_.

PRs are welcome. Please also have a look at `issues labeled with "help wanted"`_.


Local Development
=================

You can run Kubernetes Janitor against your current kubeconfig context, e.g. local `Minikube <https://github.com/kubernetes/minikube>`_:

.. code-block:: bash

    $ pipenv install --dev
    $ pipenv shell
    $ python3 -m kube_janitor --dry-run --debug --once

To run PEP8 (flake8) checks and unit tests including coverage report:

.. code-block:: bash

    $ make test


License
=======

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/.

.. _ping try_except_ on Twitter: https://twitter.com/try_except_
.. _issues labeled with "help wanted": https://github.com/hjacobs/kube-janitor/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22
