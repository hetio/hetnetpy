import warnings

import pytest


def test_relocation_warning():
    """
    https://github.com/hetio/hetio/issues/40
    """
    warnings.simplefilter('always', FutureWarning)
    with pytest.warns(FutureWarning, match='PACKAGE HAS BEEN RELOCATED'):
        import hetio.hetnet  # noqa F401
