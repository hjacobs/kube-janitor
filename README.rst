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
It processes all namespaced resources including custom resource definitions (CRDs) and will delete them
if the ``janitor/ttl`` annotation indicates the resource as expired.

Example use cases:

* Deploy the janitor to a test (non-prod) cluster and use namespaces with a TTL of 7 days (``janitor/ttl: 7d``) for prototyping
* Annotate your temporary nginx deployment with ``kubectl annotate deploy nginx janitor/ttl=24h`` to automatically delete it after 24 hours


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

The janitor is configured via command line args, environment variables and/or Kubernetes annotations.

TODO

Available command line options:

``--dry-run``
    Dry run mode: do not change anything, just print what would be done
``--debug``
    Debug mode: print more information


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
