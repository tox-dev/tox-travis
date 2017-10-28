====================================
Tox-Travis: Integrate Tox and Travis
====================================

.. image:: https://img.shields.io/pypi/v/tox-travis.svg
   :target: https://pypi.python.org/pypi/tox-travis
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/tox-travis/badge/?version=stable
   :target: https://tox-travis.readthedocs.io/en/stable/?badge=stable
   :alt: Documentation Status

.. image:: https://travis-ci.org/tox-dev/tox-travis.svg?branch=master
   :target: https://travis-ci.org/tox-dev/tox-travis

.. image:: https://codecov.io/gh/tox-dev/tox-travis/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/tox-dev/tox-travis

.. image:: https://badges.gitter.im/tox-dev/tox-travis.svg
   :alt: Join the chat at https://gitter.im/tox-dev/tox-travis
   :target: https://gitter.im/tox-dev/tox-travis?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

Tox-Travis is a plugin for Tox that simplifies the setup
between Tox and Travis.


Usage
=====

Configure the Python versions to test with in ``.travis.yml``,
and install ``tox-travis`` with pip:

.. code-block:: yaml

    sudo: false
    language: python
    python:
      - "2.7"
      - "3.4"
    install: pip install tox-travis
    script: tox

Tox will only run the ``py27`` or ``py34`` env
(or envs that have a factor that matches)
as appropriate for the version of Python
that is being run by each Travis job.
