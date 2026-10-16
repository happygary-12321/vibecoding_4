"""Supported zero-gravity and zero-restitution limits, with independent oracles.

Run from the repository root: python -B -m hw4.check_limiting
No production reference, time, or energy helpers generate expected results.
"""

import math
import sys
import unittest

from integration import complete_step, step
from state import Box, CircleState, PhysicsParameters


# <=300 position additions, scale <=30 m: 8*N*epsilon*30 <1.6e-11 m.
POSITION_ATOL = 2e-11  # m
# Velocities are constant or multiplied once; no accumulated force roundoff.
VELOCITY_ATOL = 1e-13  # m/s
ENERGY_ATOL = 1e-12  # J; a few products/subtraction at ~14 J scale
REL_TOL = 1e-13
# Positive small-e quantities use NO absolute allowance; zero cannot pass.
SMALL_REL_TOL = 1e-12


class LimitingChecks(unittest.TestCase):
    """Check limiting motion, stationary touching, and approach to e=0."""

    def close(self, actual, expected, atol, maxima, label, rtol=REL_TOL):
        self.assertTrue(math.isfinite(actual) and math.isfinite(expected))
        maxima[label] = max(maxima.get(label, 0.0), abs(actual-expected))
        self.assertTrue(math.isclose(actual, expected, abs_tol=atol, rel_tol=rtol),
                        f"{label}: actual={actual:.17g}, expected={expected:.17g}, "
                        f"atol={atol}, rtol={rtol}")

    def test_zero_gravity_uniform_motion(self):
        """Integrating dv/dt=0 gives x=x0+vx0*t and y=y0+vy0*t."""
        for advance in (step, complete_step):
            with self.subTest(entry=advance.__name__):
                p = PhysicsParameters(gravity=0.0, radius=0.25, mass=2.5,
                                      restitution=0.6, dt=0.01)
                box = Box(width=30.0, height=30.0)
                x0, y0, vx0, vy0 = 12.3, 8.4, -1.7, 2.3
                s = CircleState(x=x0, y=y0, vx=vx0, vy=vy0, step_count=0)
                maxima = {}
                for n in range(1, 301):
                    if advance is complete_step:
                        self.assertEqual(advance(s, p, box), [])
                    else:
                        advance(s, p)
                    t = n * 0.01  # independent loop time; no state.time helper
                    self.close(s.x, x0+vx0*t, POSITION_ATOL, maxima, "x_m")
                    self.close(s.y, y0+vy0*t, POSITION_ATOL, maxima, "y_m")
                    self.close(s.vx, vx0, VELOCITY_ATOL, maxima, "vx_m_per_s")
                    self.close(s.vy, vy0, VELOCITY_ATOL, maxima, "vy_m_per_s")
                    self.assertEqual(s.step_count, n)
                    self.assertGreater(s.x, p.radius)
                    self.assertLess(s.x, box.width-p.radius)
                    self.assertGreater(s.y, p.radius)
                    self.assertLess(s.y, box.height-p.radius)
                print(f"uniform {advance.__name__}: N=300, T=3 s, "
                      f"endpoint=({s.x:.12g},{s.y:.12g}) m, expected=(7.2,15.3); "
                      f"max residuals={maxima}; contacts=0", flush=True)

    def test_zero_gravity_stationary_interior(self):
        """With v0=0 and g=0, only the step counter changes."""
        for advance in (step, complete_step):
            with self.subTest(entry=advance.__name__):
                p = PhysicsParameters(gravity=0.0, radius=0.25, mass=2.5,
                                      restitution=0.6, dt=0.01)
                box = Box(width=6.0, height=5.0)
                s = CircleState(x=2.13, y=1.37, vx=0.0, vy=0.0, step_count=0)
                for n in range(1, 201):
                    if advance is complete_step:
                        self.assertEqual(advance(s, p, box), [])
                    else:
                        advance(s, p)
                    # Addition of zero preserves the stored finite values exactly.
                    self.assertEqual((s.x, s.y, s.vx, s.vy), (2.13, 1.37, 0, 0))
                    self.assertEqual(s.step_count, n)
                print(f"stationary {advance.__name__}: N=200, "
                      "position/velocity residuals=0, contacts=0", flush=True)

    def test_zero_restitution_impact_and_followup(self):
        """e=0 removes normal K, preserves tangent, and cannot rebound at g=0.

        K=m*(vn^2+vt^2)/2; vn_after=0, vt_after=vt_before. Thus
        Delta K=-m*vn_before^2/2=-12.8 J for m=2.5, |vn|=3.2.
        Stationary touching continues to emit records under SPEC's <=/>= tests.
        """
        cases = (
            ("floor", dict(x=2.0, y=0.4, vx=0.7, vy=-3.2),
             "y", "vy", "x", "vx", 1, 0.25, (0.0, 0.17)),
            ("left", dict(x=0.4, y=2.0, vx=-3.2, vy=0.7),
             "x", "vx", "y", "vy", 1, 0.25, (0.17, 0.0)),
            ("right", dict(x=5.6, y=2.0, vx=3.2, vy=0.7),
             "x", "vx", "y", "vy", -1, 5.75, (-0.17, 0.0)),
        )
        for surface, fields, axis, normal, tangent_axis, tangent, sign, bound, correction in cases:
            with self.subTest(surface=surface):
                p = PhysicsParameters(gravity=0.0, radius=0.25, mass=2.5,
                                      restitution=0.0, dt=0.1)
                box = Box(width=6.0, height=5.0)
                s = CircleState(**fields, step_count=0)
                vn_before = sign * getattr(s, normal)
                k_before = 0.5*p.mass*(s.vx*s.vx+s.vy*s.vy)
                expected_loss = -0.5*p.mass*vn_before*vn_before
                maxima = {}
                for n in range(1, 22):  # one impact plus twenty follow-up steps
                    records = complete_step(s, p, box)
                    self.assertEqual([r.surface for r in records], [surface])
                    record = records[0]
                    self.assertEqual(s.step_count, n)
                    self.assertEqual(getattr(s, axis), bound)
                    self.assertEqual(getattr(s, normal), 0.0)
                    self.close(getattr(s, tangent), 0.7, VELOCITY_ATOL,
                               maxima, "tangent_velocity_m_per_s")
                    self.close(getattr(s, tangent_axis), 2.0+0.7*n*0.1,
                               POSITION_ATOL, maxima, "tangent_position_m")
                    k_after = 0.5*p.mass*(s.vx*s.vx+s.vy*s.vy)
                    self.close(k_after, 0.6125, ENERGY_ATOL, maxima, "remaining_K_J")
                    self.assertEqual(record.normal_velocity_after, 0.0)
                    if n == 1:
                        self.assertTrue(record.is_impact)
                        self.close(record.normal_velocity_before, -3.2,
                                   VELOCITY_ATOL, maxima, "inward_velocity_m_per_s")
                        for actual, expected in zip(record.position_correction, correction):
                            self.close(actual, expected, POSITION_ATOL,
                                       maxima, "initial_correction_m")
                        self.close(k_after-k_before, expected_loss, ENERGY_ATOL,
                                   maxima, "energy_balance_J")
                        self.assertLess(k_after, k_before)
                    else:
                        self.assertFalse(record.is_impact)
                        self.assertEqual(record.normal_velocity_before, 0.0)
                        self.assertEqual(record.position_correction, (0.0, 0.0))
                print(f"e=0 {surface}: vn_after=0, K_after={k_after:.12g} J, "
                      f"dK={k_after-k_before:.12g} J; contacts=21, impacts=1; "
                      f"max residuals={maxima}", flush=True)

    def test_approach_to_zero_restitution(self):
        """For fixed vn=-3.2, outgoing speed=3.2*e and normal K=12.8*e^2."""
        previous_speed = previous_energy = float("inf")
        for e in (0.5, 0.1, 0.01, 0.001, 0.0):
            with self.subTest(restitution=e):
                p = PhysicsParameters(gravity=0.0, radius=0.25, mass=2.5,
                                      restitution=e, dt=0.1)
                box = Box(width=6.0, height=5.0)
                s = CircleState(x=2.0, y=0.4, vx=0.7, vy=-3.2, step_count=0)
                incoming = s.vy
                records = complete_step(s, p, box)
                self.assertEqual([r.surface for r in records], ["floor"])
                self.assertTrue(records[0].is_impact)
                self.assertEqual(s.step_count, 1)
                self.assertEqual(s.y, 0.25)
                speed = s.vy  # floor normal is +y; use actual state, not record
                normal_k = 0.5*2.5*speed*speed
                expected_speed = e*3.2
                expected_k = 0.5*2.5*e*e*3.2*3.2
                maxima = {}
                self.close(records[0].normal_velocity_before, -3.2,
                           VELOCITY_ATOL, maxima, "record_before_expected")
                self.close(records[0].normal_velocity_before, incoming,
                           VELOCITY_ATOL, maxima, "record_before_state")
                # Relative-only record checks preserve sensitivity at small e.
                self.close(records[0].normal_velocity_after, expected_speed, 0.0,
                           maxima, "record_after_expected", rtol=SMALL_REL_TOL)
                self.close(records[0].normal_velocity_after, speed, 0.0,
                           maxima, "record_after_state", rtol=SMALL_REL_TOL)
                self.close(s.vx, 0.7, VELOCITY_ATOL, maxima, "tangent_velocity")
                if e > 0:
                    self.assertGreater(speed, 0.0)
                    self.assertGreater(normal_k, 0.0)
                    self.close(speed, expected_speed, 0.0, maxima,
                               "speed_m_per_s", rtol=SMALL_REL_TOL)
                    self.close(normal_k, expected_k, 0.0, maxima,
                               "normal_K_J", rtol=SMALL_REL_TOL)
                else:
                    self.assertEqual(speed, 0.0)
                    self.assertEqual(normal_k, 0.0)
                self.assertLess(speed, previous_speed)
                self.assertLess(normal_k, previous_energy)
                previous_speed, previous_energy = speed, normal_k
                print(f"e={e:g}: outgoing={speed:.12g} m/s "
                      f"(expected {expected_speed:.12g}), normal_K={normal_k:.12g} J "
                      f"(expected {expected_k:.12g}); residuals="
                      f"({speed-expected_speed:.3g} m/s,{normal_k-expected_k:.3g} J)",
                      flush=True)


if __name__ == "__main__":
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
