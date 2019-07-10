import importlib

import pytest


def test_relocation_warning():
    """
    https://github.com/hetio/hetio/issues/40
    """
    with pytest.warns(FutureWarning, match='PACKAGE HAS BEEN RELOCATED'):
        import hetio
        # Reload module to ensure warning tiggers
        importlib.reload(hetio)
