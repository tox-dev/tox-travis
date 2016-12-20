"""Test utility functions and configuration for Tox-Travis."""
from tox_travis.utils import parse_dict


class TestParseDict:
    """Test the parse_dict function."""

    def test_simple(self):
        """Ensure simple cases work as expected."""
        value = """
        1.9: django19
        1.10: django110
        """
        expected = {
            '1.9': 'django19',
            '1.10': 'django110',
        }

        assert parse_dict(value) == expected

    def test_comma_separated_list(self):
        """Ensure comma-separated lists don't get split by this function."""
        value = """
        2.7: py27, docs
        3.5: py35
        """
        expected = {
            '2.7': 'py27, docs',
            '3.5': 'py35',
        }

        assert parse_dict(value) == expected

    def test_brace_no_expansion(self):
        """Ensure braces don't get expanded by this function."""
        value = """
        2.7: py27, docs
        3.5: py{35,36}
        """
        expected = {
            '2.7': 'py27, docs',
            '3.5': 'py{35,36}',
        }

        assert parse_dict(value) == expected
