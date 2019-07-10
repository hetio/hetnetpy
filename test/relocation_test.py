import importlib

import pytest


def test_relocation_warning():
    """
    https://github.com/hetio/hetio/issues/40
    """
    with pytest.warns(FutureWarning, match='package has been renamed to hetmatpy'):
        import hetio
        # Reload module to ensure warning tiggers
        importlib.reload(hetio)


@pytest.mark.filterwarnings('error')
def test_no_relocation_warning():
    """
    https://github.com/hetio/hetio/issues/40
    """
    import hetnetpy
    # Reload module to ensure warning tiggers
    importlib.reload(hetnetpy)
