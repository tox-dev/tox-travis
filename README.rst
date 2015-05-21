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
    envlist =
        py27: py27-django{17,18}
        py34: py34-django{17,18}, docs
