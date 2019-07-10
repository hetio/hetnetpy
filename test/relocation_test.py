import pytest


def test_relocation_warning():
    """
    https://github.com/hetio/hetio/issues/40
    """
    with pytest.warns(DeprecationWarning, match='PACKAGE HAS BEEN RELOCATED'):
        import hetio.hetnet  # noqa F401
