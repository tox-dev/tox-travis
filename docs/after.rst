=========
After All
=========

.. deprecated:: 0.10

.. warning::

  This feature is deprecated.

  Travis has added `Build Stages`_,
  which are a better solution to this problem.
  You will also likely want to check out `Conditions`_,
  which make it much easier to determine
  which jobs, stages, and builds will run.

.. _`Build Stages`: https://docs.travis-ci.com/user/build-stages
.. _`Conditions`: https://docs.travis-ci.com/user/conditional-builds-stages-jobs


Inspired by `travis-after-all`_ and `travis_after_all`_,
this feature allows a job to wait for other jobs to finish
before it calls itself complete.

.. _`travis-after-all`: https://github.com/alrra/travis-after-all
.. _`travis_after_all`: https://github.com/dmakhno/travis_after_all

There are three environment variables
that can be used to configure this feature.

* ``GITHUB_TOKEN``. This is *required*,
  and should be encrypted in the ``.travis.yml``,
  or set securely in the repository settings.
  This is used as the authentication method
  for the Travis CI API.
* ``TRAVIS_POLLING_INTERVAL``.
  How often, in seconds, we should check the API
  to see if the rest of the jobs have completed.
  Defaults to 5.
* ``TRAVIS_API_URL``.
  The base URL to the Travis API for this build.
  This defaults to ``https://api.travis-ci.org``.
  A common override will be to the commercial version,
  at ``https://api.travis-ci.com``.

Configure which job to wait on by adding
the ``[travis:after]`` section to the ``tox.ini`` file.
The ``travis`` key looks for values that would be keys
in various items in the ``[travis]`` section,
and the ``env`` key looks for values that would be keys
in items in the ``[travis:env]`` section.

For example:

.. code-block:: ini

    [travis:after]
    travis = python: 3.5
    env = DJANGO: 1.8

Then run ``tox`` in your test command like this::

   tox --travis-after

For example, consider this mocked up ``.travis.yml``,
that corresponds to using the above ``travis:after`` section:

.. code-block:: yaml

    sudo: false
    language: python
    python:
      - "2.6"
      - "3.5"
    env:
      global:
        - GITHUB_TOKEN='spamandeggs'  # Make sure this is encrypted!
      matrix:
        - DJANGO="1.7"
        - DJANGO="1.8"
    install: pip install tox-travis
    script: tox --travis-after
    deploy:
      provider: pypi
      user: spam
      password: eggs  # Make sure to encrypt passwords!
      on:
        tags: true
        python: 3.5
        condition: $DJANGO = "1.8"
      distributions: sdist bdist_wheel

This example deploys when the build is from a tag
and the build is on Python 3.5
and the build is using DJANGO="1.8".
Together ``tox --travis-after`` and Travis' ``on`` conditions
make sure that the deploy only happens after all tests pass.

If any configuration item does not match,
or if no configuration is given,
this will run exactly as it would normally.
However, if the configuration matches the current job,
then it will wait for all the other jobs to complete
before it will be willing to return a success return code.

If the tests fail, then it will not bother waiting,
but will rather return immediately.
If it determines that another required job has failed,
it will return an error indicating that jobs failed.

You can use this together with a deployment configuration
to ensure that this job is the very last one to complete,
and will only be successful if all others are successful,
so that you can be more confident
that you are shipping a working release.

The accepted configuration keys
in the ``[travis:after]`` section are:

* ``envlist``. Match with the running toxenvs.
  Expansion is allowed, and if set *all* environments listed
  must be run in the current Tox run.
* ``travis``. Match with known Travis factors,
  as is done in the ``[travis]`` section.
  For instance, specifying that we should wait
  when python is version 2.7 would look like
  ``travis = python: 2.7``.
* ``env``. Match with environment variable factors,
  as might be specified in the ``[travis:env]`` section.
  For instance, if we want to match that ``DJANGO`` is ``1.9``,
  then it would look like ``env = DJANGO: 1.9``.
  The value must match exactly to succeed.
