# This file is part of the pyMOR project (http://www.pymor.org).
# Copyright 2013-2020 pyMOR developers and contributors. All rights reserved.
# License: BSD 2-Clause License (http://opensource.org/licenses/BSD-2-Clause)

import os
import pymordemos  # noqa: F401
from importlib import import_module
import sys
import pytest
from tempfile import mkdtemp
import shutil

from typer import Typer
from typer.testing import CliRunner

from pymortests.base import runmodule, check_results
from pymor.core.exceptions import QtMissing, GmshMissing, MeshioMissing, TorchMissing
from pymor.discretizers.builtin.gui.qt import stop_gui_processes
from pymor.core.config import is_windows_platform, is_macos_platform
from pymor.tools.mpi import parallel


runner = CliRunner()


DISCRETIZATION_ARGS = (
    ('elliptic', [0, 0, 0, 0]),
    ('elliptic', [1, 2, 0, 3]),
    ('elliptic', ['--rect', 1, 2, 0, 3]),
    ('elliptic', [0, 0, 2, 1]),
    ('elliptic', ['--fv', 0, 0, 0, 0]),
    ('elliptic', ['--fv', 1, 2, 0, 3]),
    ('elliptic', ['--fv', '--rect', 1, 2, 0, 3]),
    ('elliptic', ['--fv', 0, 0, 2, 1]),
    ('elliptic2', [0, 20, 'h1']),
    ('elliptic2', [0, 20, 'l2']),
    ('elliptic2', [0, 20, 0.5]),
    ('elliptic2', ['--fv', 0, 20, 0]),
    ('elliptic2', [1, 20, 'h1']),
    ('elliptic2', [1, 20, 'l2']),
    ('elliptic2', [1, 20, 0.5]),
    ('elliptic_oned', [1, 20]),
    ('elliptic_oned', ['--fv', 1, 20]),
    ('burgers', ['--num-flux=lax_friedrichs', '0.1']),
    ('burgers', ['--num-flux=engquist_osher', '0.1']),
    ('burgers', ['--num-flux=simplified_engquist_osher', '0.1']),
    ('linear_optimization', [40, 20]),
    ('parabolic', ['heat', 1]),
    ('parabolic', ['heat', '--rect', 1]),
    ('parabolic', ['heat', '--fv', 1]),
    ('parabolic', ['heat', '--rect', '--fv', 1]),
    ('parabolic', ['dar', 1]),
    ('parabolic', ['dar', '--rect', 1]),
)

if not parallel:
    DISCRETIZATION_ARGS += (('elliptic_unstructured', [6., 16, 1e-1]),)
if not is_windows_platform():
    DISCRETIZATION_ARGS += (('neural_networks', [25, 50, 10]),
                            ('neural_networks_fenics', [15, 3]),
                            ('neural_networks_instationary', [25, 25, 30, 5]))

THERMALBLOCK_ARGS = (
    ('thermalblock', ['--plot-solutions', '--plot-err', '--plot-error-sequence', 2, 2, 3, 5]),
    ('thermalblock', ['--fenics', 2, 2, 3, 5]),
    ('thermalblock', ['--no-greedy-with-error-estimator', 3, 1, 2, 5]),
    ('thermalblock', ['--alg=pod', 2, 2, 3, 5]),
    ('thermalblock', ['--alg=adaptive_greedy', 2, 2, 10, 30]),
    ('thermalblock', ['--alg=naive', '--reductor=traditional', 2, 2, 10, 5]),
    ('thermalblock', ['--list-vector-array', 2, 2, 2, 2]),
)

TB_IPYTHON_ARGS = THERMALBLOCK_ARGS[0:2]

THERMALBLOCK_ADAPTIVE_ARGS = (
    ('thermalblock_adaptive', [10]),
    ('thermalblock_adaptive', ['--no-visualize-refinement', 10]),
)

THERMALBLOCK_SIMPLE_ARGS = (
    ('thermalblock_simple', ['pymor', 'naive', 2, 5, 5]),
    ('thermalblock_simple', ['fenics', 'greedy', 2, 5, 5]),
    ('thermalblock_simple', ['ngsolve', 'pod', 2, 5, 5]),
)
# Font file loading currently does not work on windows
if not is_windows_platform():
    THERMALBLOCK_SIMPLE_ARGS += (('thermalblock_simple', ['--', 'pymor_text', 'adaptive_greedy', -1, 3, 3]),)

THERMALBLOCK_GUI_ARGS = (
    ('thermalblock_gui', ['--testing', 2, 2, 3, 5]),
)
if is_windows_platform() or is_macos_platform():
    THERMALBLOCK_GUI_ARGS = tuple()

BURGERS_EI_ARGS = (
    ('burgers_ei', [1, 2, 2, 5, 2, 5, '--plot-ei-err']),
    ('burgers_ei', [1, 2, 2, 5, 2, 5, '--ei-alg=deim']),
)

PARABOLIC_MOR_ARGS = (
    ('parabolic_mor', ['pymor', 'greedy', 2, 3, 1]),
    ('parabolic_mor', ['pymor', 'pod', 2, 3, 1]),
    ('parabolic_mor', ['fenics', 'adaptive_greedy', 2, 3, 1]),
)

SYS_MOR_ARGS = (
    ('heat', [0.2, 2]),
    ('delay', [1, 2]),
    ('string_equation', [25, 2]),
    ('parametric_heat', [0.02, 2]),
    ('parametric_delay', [2]),
    ('parametric_string', [25, 2]),
    ('parametric_synthetic', [100, 2]),
)

HAPOD_ARGS = (
    ('hapod', ['--snap=3', 1e-2, 10, 100]),
    ('hapod', ['--snap=3', '--threads=2', 1e-2, 10, 100]),
    ('hapod', ['--snap=3', '--procs=2', 1e-2, 10, 100]),
)

FENICS_NONLINEAR_ARGS = (
    ('fenics_nonlinear', [2, 10, 2]),
    ('fenics_nonlinear', [3, 5, 1]),
)

DEMO_ARGS = (
    DISCRETIZATION_ARGS
    + THERMALBLOCK_ARGS
    + THERMALBLOCK_ADAPTIVE_ARGS
    + THERMALBLOCK_SIMPLE_ARGS
    + THERMALBLOCK_GUI_ARGS
    + BURGERS_EI_ARGS
    + PARABOLIC_MOR_ARGS
    + SYS_MOR_ARGS
    + HAPOD_ARGS
    + FENICS_NONLINEAR_ARGS
)
DEMO_ARGS = [(f'pymordemos.{a}', b) for (a, b) in DEMO_ARGS]


def _skip_if_no_solver(param):
    demo, args = param
    from pymor.core.config import config
    for solver in ['fenics', 'ngsolve']:
        needs_solver = len([f for f in args if solver in str(f)]) > 0 or demo.find(solver) >= 0
        has_solver = getattr(config, 'HAVE_' + solver.upper())
        if needs_solver and not has_solver:
            if not os.environ.get('DOCKER_PYMOR', False):
                pytest.skip('skipped test due to missing ' + solver)


def _skip_unsupported_torch(param):
    demo, args = param
    unsupported_py = sys.version_info[0:2] > (3, 8)
    if unsupported_py and os.environ.get('DOCKER_PYMOR', False) and 'neural_network' in demo:
        pytest.skip('skipped test due to torch unsupported on python f{sys.version_info[0:2]}')


def _demo_ids(demo_args):
    def _key(b):
        return ' '.join((str(s) for s in b))
    return [f"{a}:'{_key(b)}'".replace('pymordemos.', '') for a, b in demo_args]


@pytest.fixture(params=DEMO_ARGS, ids=_demo_ids(DEMO_ARGS))
def demo_args(request):
    _skip_if_no_solver(request.param)
    _skip_unsupported_torch(request.param)
    return request.param


@pytest.fixture(params=THERMALBLOCK_ARGS, ids=_demo_ids(THERMALBLOCK_ARGS))
def thermalblock_args(request):
    _skip_if_no_solver(request.param)
    return request.param


def _test_demo(demo):
    import sys
    sys._called_from_test = True

    def nop(*args, **kwargs):
        pass

    try:
        from matplotlib import pyplot
        pyplot.show = nop
    except ImportError:
        pass
    try:
        import dolfin
        dolfin.plot = nop
    except ImportError:
        pass

    # reset default RandomState
    import pymor.tools.random
    pymor.tools.random._default_random_state = None

    result = None
    try:
        result = demo()
    except (QtMissing, GmshMissing, MeshioMissing, TorchMissing) as e:
        if os.environ.get('DOCKER_PYMOR', False):
            # these are all installed in our CI env so them missing a grave error
            raise e
        else:
            miss = str(type(e)).replace('Missing', '')
            pytest.xfail(f'{miss} not installed')
    finally:
        stop_gui_processes()

        from pymor.parallel.default import _cleanup
        _cleanup()
        try:
            from matplotlib import pyplot
            pyplot.close('all')
        except ImportError:
            pass

    return result


def test_demos(demo_args):
    module, args = demo_args
    module = import_module(module)
    if hasattr(module, 'app'):
        app = module.app
    else:
        app = Typer()
        app.command()(module.main)
    args = [str(arg) for arg in args]
    result = _test_demo(lambda: runner.invoke(app, args, catch_exceptions=False))
    assert result.exit_code == 0


def test_analyze_pickle1():
    d = mkdtemp()
    try:
        test_demos(('pymordemos.thermalblock', ['--pickle=' + os.path.join(d, 'data'), 2, 2, 2, 10]))
        test_demos(('pymordemos.analyze_pickle',
                   ['histogram', '--error-norm=h1_0_semi', os.path.join(d, 'data_reduced'), 10]))
    finally:
        shutil.rmtree(d)


def test_analyze_pickle2():
    d = mkdtemp()
    try:
        test_demos(('pymordemos.thermalblock', ['--pickle=' + os.path.join(d, 'data'), 2, 2, 2, 10]))
        test_demos(('pymordemos.analyze_pickle',
                   ['histogram', '--detailed-data=' + os.path.join(d, 'data_detailed'), os.path.join(d, 'data_reduced'),
                    10]))
    finally:
        shutil.rmtree(d)


def test_analyze_pickle3():
    d = mkdtemp()
    try:
        test_demos(('pymordemos.thermalblock', ['--pickle=' + os.path.join(d, 'data'), 2, 2, 2, 10]))
        test_demos(('pymordemos.analyze_pickle',
                   ['convergence', '--error-norm=h1_0_semi', os.path.join(d, 'data_reduced'),
                    os.path.join(d, 'data_detailed'), 10]))
    finally:
        shutil.rmtree(d)


def test_analyze_pickle4():
    d = mkdtemp()
    try:
        test_demos(('pymordemos.thermalblock', ['--pickle=' + os.path.join(d, 'data'), 2, 2, 2, 10]))
        test_demos(('pymordemos.analyze_pickle',
                   ['convergence', os.path.join(d, 'data_reduced'),
                    os.path.join(d, 'data_detailed'), 10]))
    finally:
        shutil.rmtree(d)


@pytest.mark.skipif(is_windows_platform(), reason='hangs indefinitely')
@pytest.mark.skipif(is_macos_platform(), reason='spurious JSON Decode errors in Ipython launch')
@pytest.mark.parametrize('ipy_args', TB_IPYTHON_ARGS)
def test_thermalblock_ipython(ipy_args):
    _skip_if_no_solver(ipy_args)
    from pymor.tools import mpi
    if mpi.parallel:  # simply running 'ipcluster start' (without any profile) does not seem to work
        return        # when running under mpirun, so we do not test this combination for now
    try:
        test_demos((f'pymordemos.{ipy_args[0]}', ['--ipython-engines=2'] + ipy_args[1]))
    finally:
        import time     # there seems to be no way to shutdown the IPyhton cluster s.t. a new
        time.sleep(10)  # cluster can be started directly afterwards, so we have to wait ...


def test_thermalblock_results(thermalblock_args):
    from pymordemos import thermalblock
    app = Typer()
    app.command()(thermalblock.main)
    args = [str(arg) for arg in thermalblock_args[1]]
    _test_demo(lambda: runner.invoke(app, args, catch_exceptions=False))
    results = thermalblock.test_results
    # due to the symmetry of the problem and the random test parameters, the estimated
    # error may change a lot
    # fenics varies more than others between MPI/serial
    first_tolerance = (1e-13, 3.5e-6) if '--fenics' in thermalblock_args[1] else (1e-13, 1e-7)
    check_results('test_thermalblock_results', thermalblock_args[1], results,
                  first_tolerance, 'basis_sizes', 'norms', 'max_norms',
                  (1e-13, 4.), 'errors', 'max_errors', 'rel_errors', 'max_rel_errors',
                  'error_estimates', 'max_error_estimates', 'effectivities',
                  'min_effectivities', 'max_effectivities', 'errors')


def test_burgers_ei_results():
    from pymordemos import burgers_ei
    app = Typer()
    app.command()(burgers_ei.main)
    args = list(map(str, [1, 2, 10, 100, 10, 30]))
    _test_demo(lambda: runner.invoke(app, args, catch_exceptions=False))
    ei_results, greedy_results = burgers_ei.test_results
    ei_results['greedy_max_errs'] = greedy_results['max_errs']
    check_results('test_burgers_ei_results', args, ei_results,
                  (1e-13, 1e-7), 'errors', 'triangularity_errors', 'greedy_max_errs')


def test_parabolic_mor_results():
    from pymordemos import parabolic_mor
    args = ['pymor', 'greedy', 5, 20, 3]
    results = _test_demo(lambda: parabolic_mor.main(*args))
    check_results('test_parabolic_mor_results', args, results,
                  (1e-13, 1e-7), 'basis_sizes', 'norms', 'max_norms',
                  (1e-13, 4.), 'errors', 'max_errors', 'rel_errors', 'max_rel_errors',
                  'error_estimates', 'max_error_estimates', 'effectivities',
                  'min_effectivities', 'max_effectivities', 'errors')


if __name__ == "__main__":
    runmodule(filename=__file__)
