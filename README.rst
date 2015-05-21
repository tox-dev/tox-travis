=====================================
tox-travis: Integrate Tox into Travis
=====================================

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
which are ``py27`` and ``py34`` in the example above.


Advanced Configuration
======================

To customize what environments tox will run on Travis,
add a section to ``tox.ini`` telling it what environments
to run under which versions of Python:

.. code-block:: ini

    [tox]
    envlist = py{27,34}-django{17,18}, docs

    [tox:travis]
    2.7 = py27-django{17,18}
    3.4 = py34-django{17,18}, docs

Note that Travis won't run all the envs simultaneously,
because it's build matrix is only aware of the Python versions.
Only one Travis build will be run per Python version,
unless other settings are sepecified in the Travis build matrix.
