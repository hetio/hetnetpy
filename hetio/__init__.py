import warnings

__version__ = "0.2.11"

message = '''
PACKAGE HAS BEEN RELOCATED:
v0.2.11 is the last release before the hetio package is renamed to hetnetpy.
Consider switching to the hetnetpy package or specifying hetio<=0.2.10 to silence this warning.
Future releases and development will only occur for the hetnetpy package.
'''
warnings.warn(message, FutureWarning)
