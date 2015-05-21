==========
tox-travis
==========

Seamless integration of Tox into Travis CI.


Usage
=====

Configure the Python versions to test with in ``travis.yml``:

.. code-block:: yml

    sudo: false
    language: python
    python:
      - "2.7"
      - "3.4"
    install: pip install tox-travis
    script: tox

Then add a section to ``tox.ini``, telling it what environments to run
under which versions of Python:

.. code-block:: ini

    [tox]
    envlist = py{27,34}-django{17,18}, docs

    [tox:travis]
    2.7 = py27-django{17,18}
    3.4 = py34-django{17,18}, docs

If the version that Travis is running isn't avaliable,
it'll use these defaults:

.. code-block:: ini

    [tox:travis]
    2.6 = py26
    2.7 = py27
    3.2 = py32
    3.3 = py33
    3.4 = py34
    3.5 = py35
    pypy = pypy
    pypy3 = pypy3
