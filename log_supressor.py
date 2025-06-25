import sys
import os
import contextlib

@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, 'w') as fnull:
        old_stderr = sys.stderr
        sys.stderr = fnull
        try:
            yield
        finally:
            sys.stderr = old_stderr