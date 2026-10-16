"""Meaningful gaps found by the HW4 function audit; standard-library unittest.

Outputs use TemporaryDirectory; GUI orchestration uses a fake backend, never
a native window. Real plotting remains covered by check_cli's subprocess test.
"""

import builtins
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
import io
import json
import math
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

from contacts import resolve_contacts
from integration import complete_step
import make_figures
import rendering
from state import Box, CircleState, PhysicsParameters
import validation as v


class FunctionCoverageChecks(unittest.TestCase):
    """Check observable results, rejection boundaries, and error propagation."""

    def close(self, actual, expected):
        # <=6 steps/energies below 100: 1e-12 SI covers arithmetic roundoff.
        self.assertTrue(math.isfinite(actual))
        self.assertAlmostEqual(actual, expected, delta=1e-12)

    def test_state_type_validation_and_mutation(self):
        for constructor, field in ((CircleState, "x"), (PhysicsParameters, "mass"),
                                   (Box, "width")):
            for value in (True, "2", None):
                with self.subTest(constructor=constructor.__name__, value=value):
                    with self.assertRaises(ValueError):
                        constructor(**{field: value})
        for field, value in (("vy", float("nan")), ("x", True),
                             ("step_count", True), ("step_count", -2)):
            s = CircleState()
            setattr(s, field, value)
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                s.validate()
        s = CircleState(x=-2, y=15, vx=-3, vy=4, step_count=7)
        before = replace(s)
        self.assertIsNone(s.validate())  # legal outside geometry as numeric data
        self.close(s.time(PhysicsParameters(dt=0.125)), 0.875)
        self.assertEqual(s, before)

    def test_invalid_geometry_rejected_before_mutation(self):
        p = PhysicsParameters(radius=0.3, dt=0.1)
        for box in (Box(width=0.6, height=2), Box(width=2, height=0.6)):
            for operation in (complete_step, resolve_contacts):
                s = CircleState(x=0.1, y=0.1, vx=-2, vy=-3, step_count=5)
                before = replace(s)
                with self.subTest(operation=operation.__name__, box=box):
                    with self.assertRaises(ValueError):
                        operation(s, p, box)
                    self.assertEqual(s, before)
            with self.assertRaises(ValueError):
                rendering.FixedStepScheduler(CircleState(), p, box)
        bad = CircleState()
        bad.vx = float("inf")
        with self.assertRaises(ValueError):
            rendering.FixedStepScheduler(bad, p, Box())

    def test_scheduler_rounding_physics_and_overflow(self):
        # The quotient is just below 2: snap within 8 ulps, floor beyond it.
        for ulps, expected_steps in ((4, 2), (16, 1)):
            with self.subTest(ulps=ulps):
                elapsed = 2.0 - ulps*math.ulp(2.0)
                s = CircleState(x=10, y=10, vx=1.5, vy=2)
                p = PhysicsParameters(dt=1.0, gravity=0, radius=0.25)
                scheduler = rendering.FixedStepScheduler(s, p, Box(100, 100))
                self.assertEqual(scheduler.advance(elapsed), expected_steps)
                self.assertEqual(s.step_count, expected_steps)
                self.close(s.x, 10+1.5*expected_steps)
                self.close(s.y, 10+2*expected_steps)
                self.close(scheduler.accumulator, max(0, elapsed-expected_steps))
                self.assertEqual(scheduler.elapsed_time, elapsed)
                self.assertEqual(scheduler.discarded_steps, 0)
                self.assertEqual(scheduler.discarded_time, 0)
                self.assertEqual(scheduler.advance(0.25), 0 if ulps == 4 else 1)
                self.assertEqual(s.step_count, 2)
                self.close(scheduler.accumulator, 0.25 if ulps == 4 else elapsed-1.75)
                self.close(scheduler.elapsed_time, elapsed+0.25)
        s = CircleState()
        scheduler = rendering.FixedStepScheduler(s, PhysicsParameters(dt=1e-308), Box())
        with self.assertRaisesRegex(ValueError, "too large"):
            scheduler.advance(1e308)
        self.assertEqual(s.step_count, 0)
        self.assertEqual((scheduler.accumulator, scheduler.elapsed_time,
                          scheduler.discarded_time, scheduler.discarded_steps), (0, 0, 0, 0))

    def test_repeated_overload_accumulates_discarded_time(self):
        """Two overloads discard 10 then 20 steps, never replaying backlog."""
        s = CircleState(x=10, y=10, vx=0.5, vy=0.25, step_count=7)
        p = PhysicsParameters(gravity=0, dt=0.125)
        scheduler = rendering.FixedStepScheduler(s, p, Box(100, 100))
        # Binary-exact seconds: 70.5 steps, then 80.25 including remainder,
        # then exactly one step. Expectations count only newly executed steps.
        for elapsed, count, executed, dropped, remainder, total in (
            (8.8125, 60, 60, 10, 0.0625, 8.8125),
            (9.96875, 60, 120, 30, 0.03125, 18.78125),
            (0.09375, 1, 121, 30, 0.0, 18.875),
            (0.0, 0, 121, 30, 0.0, 18.875),
        ):
            with self.subTest(elapsed=elapsed):
                self.assertEqual(scheduler.advance(elapsed), count)
                self.assertEqual(s.step_count, 7 + executed)
                self.assertEqual((s.x, s.y), (10 + executed/16, 10 + executed/32))
                self.assertEqual((s.vx, s.vy), (0.5, 0.25))
                self.assertEqual(scheduler.discarded_steps, dropped)
                self.assertEqual(scheduler.discarded_time, dropped/8)
                self.assertEqual(scheduler.accumulator, remainder)
                self.assertEqual(scheduler.elapsed_time, total)
                self.assertEqual(total, executed/8 + dropped/8 + remainder)

    def test_side_walls_above_displayed_height(self):
        """Finite display height does not disable either side-wall response."""
        p = PhysicsParameters(radius=0.25, restitution=0.5)
        for x, vx, bound, outgoing, surface, dx in (
            (0.125, -3, 0.25, 1.5, "left", 0.125),
            (5.875, 3, 5.75, -1.5, "right", -0.125),
        ):
            with self.subTest(surface=surface):
                s = CircleState(x=x, y=8, vx=vx, vy=2, step_count=9)
                records = resolve_contacts(s, p, Box(6, 3))
                self.assertEqual((s.x, s.y, s.vx, s.vy, s.step_count),
                                 (bound, 8, outgoing, 2, 9))
                self.assertEqual(len(records), 1)
                record = records[0]
                self.assertEqual(record.surface, surface)
                self.assertEqual(record.position_correction, (dx, 0))
                self.assertEqual(record.normal_velocity_before, -3)
                self.assertEqual(record.normal_velocity_after, 1.5)
                self.assertTrue(record.is_impact)

    def test_whole_steps_boundaries_and_rejections(self):
        for duration, expected in ((1.0, 1), (1_000_000.0, 1_000_000),
                                   (10+4*math.ulp(10.0), 10)):
            self.assertEqual(v.whole_steps(duration, 1.0, "duration"), expected)
        for duration, dt in ((0, 1), (-1, 1), (math.nan, 1), (1, 0),
                             (1, math.inf), (0.1, 1), (10+16*math.ulp(10.0), 1),
                             (1_000_001, 1), (1e308, 1e-308)):
            with self.subTest(duration=duration, dt=dt), self.assertRaises(ValueError):
                v.whole_steps(duration, dt, "duration")

    def test_experiment_counts_and_discrete_floor_guard(self):
        self.assertEqual(v.validate_experiments(0.125, 0.5, 2), (4, 8, 16))
        # At T=1 exact y=5.095, but h=1 Euler y=.19 <= radius .2.
        for dt, duration, bounce in ((1, 1, 1), (0.5, 1.5, 2),
                                     (1e-6, 0.6, 0.1), (0.1, 0.2, 0.25)):
            with self.subTest(dt=dt, duration=duration), self.assertRaises(ValueError):
                v.validate_experiments(dt, duration, bounce)

    def test_check_helpers_and_tolerance_policy(self):
        self.assertEqual(v.tolerance(1e-10, 2, 0.5), 1e-10)
        self.assertEqual(v.tolerance(0, 1, 0.5), 2.0**-49)
        self.assertEqual(v.tolerance(1e-12, 1024, 1024), 2.0**-29)
        checks = []
        for measured in (1.125, 0.875, math.nextafter(1.125, math.inf), math.nan, math.inf):
            self.assertIsNone(v.check_close(checks, "boundary", measured, 1, 0.125))
        self.assertEqual([c["passed"] for c in checks], [True, True, False, False, False])
        self.assertEqual(checks[0], dict(name="boundary", measured=1.125, expected=1,
                                       residual=0.125, tolerance=0.125, passed=True))
        v.check_true(checks, "empty", [])
        v.check_true(checks, "nonempty", [0])
        self.assertEqual(checks[-2], dict(name="empty", measured=False, expected=True, passed=False))
        self.assertEqual(checks[-1], dict(name="nonempty", measured=True, expected=True, passed=True))

    def test_sample_is_independent_snapshot(self):
        s = CircleState(x=1.2, y=2, vx=-3, vy=4, step_count=7)
        before = replace(s)
        row = v.sample(s, PhysicsParameters(mass=2.5, gravity=9.81, dt=0.125))
        expected = dict(x=1.2, y=2, vx=-3, vy=4, step_count=7, time=0.875, energy=80.3)
        self.assertEqual(set(row), set(expected))
        for key, value in expected.items():
            self.close(row[key], value)
        self.assertEqual(s, before)
        s.x = 99
        self.assertEqual(row["x"], 1.2)
        row["vy"] = 100
        self.assertEqual(s.vy, 4)

    def test_free_fall_report_against_independent_solution(self):
        checks = []
        run = v.free_fall(PhysicsParameters(mass=3, gravity=2, dt=0.125), 4, checks, "audit")
        self.assertEqual(len(run["samples"]), 5)
        for n, row in enumerate(run["samples"]):
            t = n/8
            y = 10-n*(n+1)/64  # sum of k/32 displacements
            self.close(row["time"], t)
            self.assertEqual(row["step_count"], n)
            self.close(row["y"], y)
            self.close(row["vy"], -2*t)
            self.close(row["exact_height"], 10-t*t)
            self.close(row["signed_error"], -t/8)
            self.close(row["energy"], 6*y+1.5*(2*t)**2)
            self.close(row["measured_energy_drift"], -3*t/4)
            self.close(row["expected_energy_drift"], -3*t/4)
        self.assertEqual(run["final"], run["samples"][-1])
        self.assertTrue(checks and all(c["passed"] for c in checks))

    def test_bouncing_report_independent_first_impact_accounting(self):
        # Defaults x=1,y=2,vx=1.5,vy=0. g=2,h=.25: first floor at step 5,
        # pre-y=.125, pre-vy=-2.5; r=.25 projects by .125, adding .75 J.
        for e, final_y, final_vy, loss, final_energy in (
            (0.5, 0.4375, 0.75, -7.03125, 6.84375),
            (1.0, 0.75, 2.0, 0.0, 13.875),
        ):
            with self.subTest(e=e):
                checks = []
                run = v.bouncing(PhysicsParameters(mass=3, gravity=2, dt=0.25,
                                                    radius=0.25, restitution=e), 6, checks, "audit")
                self.assertEqual(run["impact_counts"], dict(floor=1, left=0, right=0))
                self.assertEqual(len(run["contacts"]), 1)
                record = run["contacts"][0]
                self.assertEqual((record["surface"], record["step_count"]), ("floor", 5))
                for key, value in dict(time=1.25, normal_velocity_before=-2.5,
                                       normal_velocity_after=2.5*e,
                                       measured_kinetic_change=loss,
                                       expected_restitution_loss=loss,
                                       correction_energy=0.75).items():
                    self.close(record[key], value)
                self.assertEqual(record["position_correction"], (0, 0.125))
                final = run["samples"][-1]
                for key, value in dict(x=3.25, y=final_y, vx=1.5, vy=final_vy,
                                       energy=final_energy, cumulative_integration_drift=-2.25,
                                       cumulative_restitution_loss=loss,
                                       cumulative_correction_energy=0.75).items():
                    self.close(final[key], value)
                self.close(final["energy"]-15.375, -2.25+loss+0.75)
                self.assertTrue(checks and all(c["passed"] for c in checks))

    def test_contact_direction_report(self):
        checks = []
        result = v.contact_direction(checks)
        self.close(result["measured_y"], 0.2)
        self.close(result["measured_correct_vy"], 2.0)
        self.assertFalse(result["correct_is_impact"])
        self.close(result["illustrative_faulty_vy"], -1.6)
        self.assertEqual(len(checks), 3)
        self.assertTrue(all(c["passed"] for c in checks))

    def test_embedded_regression_report(self):
        with TemporaryDirectory() as directory:
            result = v.regression_checks(Path(directory))
            self.assertEqual(result, dict(tests_run=11, passed=True, failures=[], errors=[]))
            output = (Path(directory)/"regression_checks.txt").read_text(encoding="utf-8")
            self.assertIn("test_free_fall_and_refinement", output)
            self.assertIn("test_default_trajectory", output)
            self.assertIn("Ran 11 tests", output)

    def test_validation_failure_serialization_and_invalid_setup(self):
        with TemporaryDirectory() as directory:
            invalid = Path(directory)/"invalid"
            with self.assertRaises(ValueError):
                v.run_validation(invalid, 0.8, 0, 0.2, 0.2)
            self.assertFalse(invalid.exists())
            # Controlled I/O failure, not a production bug: exercise documented
            # exception-to-failed-report behavior without writing any plots.
            with patch.object(v, "write_plots", side_effect=OSError("audit write error")):
                result = v.run_validation(Path(directory)/"failed", 0.8, 0.02, 0.2, 0.2)
            saved = json.loads((Path(directory)/"failed"/"results.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "failed")
            self.assertEqual(result["status"], "failed")
            self.assertIn("audit write error", saved["exception"])
            self.assertEqual(saved["figures"], [])
            self.assertEqual(len(saved["free_fall"][0]["samples"]), 11)
            self.assertTrue(saved["regressions"]["passed"])

    def test_figure_entry_dispatch_and_failures(self):
        with TemporaryDirectory() as directory:
            options = ["--output-dir", directory, "--dt", "0.02", "--duration", "0.2",
                       "--bounce-duration", "0.4", "--restitution", "0.3"]
            report = dict(status="failed", checks=[dict(name="audit", passed=False)],
                          exception="audit experiment failure")
            stderr = io.StringIO()
            with patch.object(make_figures, "run_validation", return_value=report) as run, \
                    redirect_stderr(stderr):
                self.assertEqual(make_figures.main(options), 1)
            run.assert_called_once_with(directory, 0.3, 0.02, 0.2, 0.4)
            self.assertIn("Validation FAILED", stderr.getvalue())
            self.assertIn("audit experiment failure", stderr.getvalue())
            with patch.object(make_figures, "run_validation", side_effect=OSError("disk error")), \
                    redirect_stderr(io.StringIO()) as output:
                self.assertEqual(make_figures.main(options), 1)
            self.assertIn("Cannot write validation evidence", output.getvalue())
            with patch.object(make_figures, "run_validation", side_effect=ValueError("unexpected")):
                with self.assertRaisesRegex(ValueError, "unexpected"):
                    make_figures.main(options)

    def test_rendering_dependency_classification(self):
        original = builtins.__import__
        for missing in ("pyvista", "vtkmodules", "unrelated_package"):
            def intercept(name, *args, **kwargs):
                if name == "pyvista":
                    raise ModuleNotFoundError("audit missing", name=missing)
                return original(name, *args, **kwargs)
            with self.subTest(missing=missing), patch("builtins.__import__", side_effect=intercept):
                expected = (ModuleNotFoundError if missing == "unrelated_package"
                            else rendering.RenderingDependencyError)
                with self.assertRaises(expected):
                    rendering.run_simulation(PhysicsParameters())

    def test_runner_includes_both_directories_and_fails_closed(self):
        """Synthetic temporary suites verify discovery and process exit status."""
        runner = Path(__file__).with_name("run_tests.py").read_text(encoding="utf-8")
        passing = "import unittest\nclass Probe(unittest.TestCase):\n    def test_probe(self):\n        self.assertEqual(2+3, 5)\n"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"hw4").mkdir()
            (root/"hw4"/"run_tests.py").write_text(runner, encoding="utf-8")
            (root/"check_root.py").write_text(passing, encoding="utf-8")
            probe = root/"hw4"/"check_probe.py"
            for source, exit_code, marker in (
                (passing, 0, "Ran 2 tests"),
                ("import unittest\nclass Probe(unittest.TestCase):\n    def test_probe(self):\n        self.fail('synthetic runner failure')\n", 1, "synthetic runner failure"),
                ("raise ImportError('synthetic import error')\n", 1, "synthetic import error"),
            ):
                with self.subTest(marker=marker):
                    probe.write_text(source, encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", "-m", "hw4.run_tests"],
                                            cwd=root, capture_output=True, text=True)
                    self.assertEqual(result.returncode, exit_code, result.stdout+result.stderr)
                    self.assertIn(marker, result.stdout+result.stderr)
                    if exit_code == 0:
                        self.assertIn("Included check_root: 1 tests", result.stdout)
                        self.assertIn("Included hw4.check_probe: 1 tests", result.stdout)

    def test_rendering_callback_physics_and_cleanup(self):
        for mode in ("normal", "timer_failure", "callback_failure"):
            with self.subTest(mode=mode):
                plotter = MagicMock()
                actor, status = SimpleNamespace(position=None), Mock()
                plotter.add_mesh.return_value = actor
                plotter.add_text.side_effect = [Mock(), status]
                plotter.iren.create_timer.return_value = 0 if mode == "timer_failure" else 1
                backend = SimpleNamespace(Plotter=Mock(return_value=plotter), Disc=Mock(),
                                          Line=Mock(), __version__="fake", vtk_version_info=(0, 0, 0))
                def show(**kwargs):
                    callback = plotter.iren.add_observer.call_args.args[1]
                    for _ in range(3):
                        callback(None, None)
                        if mode == "callback_failure":
                            break
                plotter.show.side_effect = show
                if mode == "callback_failure":
                    plotter.render.side_effect = ValueError("audit callback error")
                output = io.StringIO()
                with patch.dict("sys.modules", {"pyvista": backend}), \
                        patch.object(rendering, "perf_counter", side_effect=[0, 0.25, 0.5]), \
                        redirect_stdout(output):
                    if mode == "normal":
                        rendering.run_simulation(PhysicsParameters(gravity=2, dt=0.125))
                    else:
                        expected = RuntimeError if mode == "timer_failure" else ValueError
                        with self.assertRaises(expected):
                            rendering.run_simulation(PhysicsParameters(gravity=2, dt=0.125))
                plotter.close.assert_called_once()
                if mode == "normal":
                    # First event starts clock; next two integrate 4 real steps.
                    self.assertEqual(actor.position, (1.75, 1.6875, 0))
                    self.assertIn("steps=4, simulation=0.5 s", output.getvalue())
                    self.assertIn("Simulation: 0.50 s", status.SetInput.call_args.args[0])
                    self.assertEqual(plotter.render.call_count, 3)
                elif mode == "timer_failure":
                    plotter.show.assert_not_called()
                else:
                    plotter.iren.terminate_app.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
