__version__ = "0.3.0"

if __name__ == "hetio":
    # https://github.com/hetio/hetnetpy/issues/40
    import warnings
    message = (
        "The 'hetio' package has been renamed to 'hetmatpy'. "
        "Future versions will remove the ability to 'import hetio'. "
        "Switch to 'import hetmatpy'."
    )
    warnings.warn(message, FutureWarning)
