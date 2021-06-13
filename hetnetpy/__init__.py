if __name__ == "hetio":
    # https://github.com/hetio/hetnetpy/issues/40
    import warnings

    message = (
        "The 'hetio' package has been renamed to 'hetnetpy'. "
        "Future versions will remove the ability to 'import hetio'. "
        "Switch to 'import hetnetpy'."
    )
    warnings.warn(message, FutureWarning)
