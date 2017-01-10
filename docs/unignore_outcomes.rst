=================
Unignore Outcomes
=================

By default, when using ``ignore_outcome`` in your Tox configuration,
any build errors will show as successful on Travis. This might not
be desired, as you might want to control allowed failures inside your
``.travis.yml``. To cater this need, you can set ``unignore_outcomes``
to ``True``. This will override ``ignore_outcome`` by setting it to
``False`` for all environments.


Usage
=====

Configure the allowed failures in the build matrix in your ``travis.yml``:

.. code-block:: yaml

    matrix:
      allow_failures:
      - python: 3.6
        env: DJANGO=master

And in your ``tox.ini``:

.. code-block:: ini

    [travis]
    unignore_outcomes = True
