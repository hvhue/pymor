
def iadd_masked(U, V, U_ind):
    """This cython function is defined in pymor/discretizers/builtin/inplace.pyx."""


def isub_masked(U, V, U_ind):
    """This cython function is defined in pymor/discretizers/builtin/inplace.pyx."""


raise ImportError('''
Cython extension module 'pymor.tools.inplace' has not been built.
Please run 'python setup.py build_ext --inplace' in the root
directory of the pyMOR repository.''')
