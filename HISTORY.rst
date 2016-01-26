0.3 (2016-01-26)
++++++++++++++++

* Match against testenvs that are only declared as sections (#7)
  thanks to @epsy
* Include unmatched envs verbatim to run (also #7)
  thanks to @epsy again


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
