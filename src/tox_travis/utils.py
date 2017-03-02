"""Shared constants and utility functions."""

# Mapping Travis factors to the associated env variables
TRAVIS_FACTORS = {
    'os': 'TRAVIS_OS_NAME',
    'language': 'TRAVIS_LANGUAGE',
    'python': 'TRAVIS_PYTHON_VERSION',
}


def parse_dict(value):
    """Parse a dict value from the tox config.

    .. code-block: ini

        [travis]
        python =
            2.7: py27, docs
            3.5: py{35,36}

    With this config, the value of ``python`` would be parsed
    by this function, and would return::

        {
            '2.7': 'py27, docs',
            '3.5': 'py{35,36}',
        }

    """
    lines = [line.strip() for line in value.strip().splitlines()]
    pairs = [line.split(':', 1) for line in lines if line]
    return dict((k.strip(), v.strip()) for k, v in pairs)
