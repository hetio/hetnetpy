import importlib
import platform

import pytest


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="symlink hetio directory does not install as package on Windows",
)
def test_relocation_warning():
    """
    https://github.com/hetio/hetnetpy/issues/40
    """
    with pytest.warns(FutureWarning, match="package has been renamed to 'hetnetpy'"):
        import hetio

        # Reload module to ensure warning tiggers
        importlib.reload(hetio)


@pytest.mark.filterwarnings("error")
def test_no_relocation_warning():
    """
    https://github.com/hetio/hetnetpy/issues/40
    """
    import hetnetpy

    # Reload module to ensure warning tiggers
    importlib.reload(hetnetpy)
