0.7 (TBD)
+++++++++

* Deprecate the ``[tox:travis]`` section in favor of
  the ``python`` key to the new ``[travis]`` section.
* Allow specifying envs by other Travis factors.
  Includes ``os``, ``language``, and ``python``.
* Allow specifying envs for environment variables,
  in a new ``[travis:env]`` section.
* Special thanks to @rpkibly for driving this work (#34)
* Backward incompatible changes:

  * If *any* declared tox envs match the envs matched from factors,
    no additional envs will be included automatically.
    For example, if ``envlist`` is ``docs``,
    and the configuration for python 3.4 is ``py34, docs``,
    it previously would have run both the declared ``docs`` env,
    as well as the undeclared ``py34`` env,
    while now it will only run the declared ``docs`` env.
    This may result in *fewer* envs running than expected,
    but in edge cases that were believed to be unlikely.
  * Previously, if no Python version was given in the environment,
    it would automatically choose an appropriate env
    based on the Python version running.
    Now if no Python version is given in the environment
    no env is determined by default,
    which may result in *more* envs running in a job than expected.

* Add the ``--travis-after`` command to enable
  a job to wait until all others have completed. (#13)
  - thanks to @ssbarnea for the feature suggestion.

0.6 (2016-10-13)
++++++++++++++++

* Require pytest<3 for Python 3.2 (#33)

0.5 (2016-07-28)
++++++++++++++++

* Prefer ``TRAVIS_PYTHON_VERSION`` to sys.version_info (#14)
  - thanks to @jayvdb for the code review
* Add Python 3.2 support (#17)
  - thanks to @jayvdb for the bug report, discussion, and code review
* Support PyPy3 v5.2 with setuptools hackery (#24)
  - thanks to @jayvdb for the pull request

0.4 (2016-02-10)
++++++++++++++++

* Generate default env from sys.version_info (#9)
  - thanks to @jayvdb for the bug report


0.3 (2016-01-26)
++++++++++++++++

* Match against testenvs that are only declared as sections (#7)
  - thanks to @epsy
* Include unmatched envs verbatim to run (also #7)
  - thanks to @epsy again


0.2 (2015-12-10)
++++++++++++++++

* Choose testenvs from ``tox.ini`` by matching factors.

  * This is a slightly *backward incompatible* change
  * If a Python version isn't declared in the ``tox.ini``,
    it may not be run.
  * Additional envs may be run if they also match the factors,
    for example, ``py34-django17`` and ``py34-django18`` will
    both match the default for Python 3.4 (``py34``).
  * Factor matching extends to overrides set in ``tox.ini``.


0.1 (2015-05-21)
++++++++++++++++

* Initial Release
