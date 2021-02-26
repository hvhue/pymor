from pymor.core.exceptions import CythonExtensionNotBuiltError


def iadd_masked(U, V, U_ind):
    """This cython function is defined in pymor/discretizers/builtin/inplace.pyx."""
    raise CythonExtensionNotBuiltError()


def isub_masked(U, V, U_ind):
    """This cython function is defined in pymor/discretizers/builtin/inplace.pyx."""
    raise CythonExtensionNotBuiltError()
