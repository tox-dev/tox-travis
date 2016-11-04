from tox_travis import parse_dict


class TestParseDict:

    def test_simple(self):
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
        value = """
        2.7: py27, docs
        3.5: py{35,36}
        """
        expected = {
            '2.7': 'py27, docs',
            '3.5': 'py{35,36}',
        }

        assert parse_dict(value) == expected
