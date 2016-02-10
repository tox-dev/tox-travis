=====================================
tox-travis: Integrate Tox into Travis
=====================================

.. image:: https://img.shields.io/pypi/v/tox-travis.svg
    :target: https://pypi.python.org/pypi/tox-travis
    :alt: Latest Version

.. image:: https://travis-ci.org/ryanhiebert/tox-travis.svg?branch=master
    :target: https://travis-ci.org/ryanhiebert/tox-travis

.. image:: https://badges.gitter.im/ryanhiebert/tox-travis.svg
   :alt: Join the chat at https://gitter.im/ryanhiebert/tox-travis
   :target: https://gitter.im/ryanhiebert/tox-travis?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

tox-travis is a simple plugin for tox that allows you to use
Travis CI's multiple python version feature as well as tox's
full configurability in a straightforward way.


Usage
=====

Configure the Python versions to test with in ``travis.yml``:

.. code-block::

    sudo: false
    language: python
    python:
      - "2.7"
      - "3.4"
    install: pip install tox-travis
    script: tox

And it will run the appropriate testenvs,
which by default are any declared env with
``py27`` or ``py34`` as factors of the name.
If no environments match a given factor,
the ``py27`` or ``py34`` envs are used as a fallback.


Advanced Configuration
======================

To customize what environments tox will run on Travis,
add a section to ``tox.ini`` telling it what environments
to run under which versions of Python:

.. code-block:: ini

    [tox]
    envlist = py{27,34}-django{17,18}, docs

    [tox:travis]
    2.7 = py27
    3.4 = py34, docs

This would run the Python 2.7 variants under 2.7,
and the Python 3.4 variants and the ``docs`` env under 3.4.

Note that Travis won't run all the envs simultaneously,
because it's build matrix is only aware of the Python versions.
Only one Travis build will be run per Python version,
unless other settings are specified in the Travis build matrix.
