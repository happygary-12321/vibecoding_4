"""Measure smooth-flight convergence against an independent exact solution.

Run from the repository root: python -B -m hw4.check_convergence
This test does not establish convergence order across collisions.
"""

import math
import sys
import unittest

from integration import complete_step, step
from state import Box, CircleState, PhysicsParameters


# <=192 steps, position/velocity scales <25 SI: 8*N*epsilon*25 <8.6e-12.
# These allowances cover roundoff only, not the O(h) vertical position error.
POSITION_ATOL = 1e-11  # m
VELOCITY_ATOL = 1e-11  # m/s
REL_TOL = 1e-13
# Propagating 1e-11 m into log2(E_coarse/E_fine) for the finest pair gives
# (1e-11/0.1149609375 + 1e-11/0.05748046875)/ln(2) <3.8e-10.
# 1e-9 adds margin for the ratio/log evaluation, with no broad order window.
ORDER_ATOL = 1e-9  # dimensionless, absolute only


class ConvergenceChecks(unittest.TestCase):
    """Check first-order vertical-position error for both integration APIs."""

    def close(self, actual, expected, atol):
        self.assertTrue(math.isfinite(actual) and math.isfinite(expected))
        self.assertTrue(math.isclose(actual, expected, abs_tol=atol,
                                     rel_tol=REL_TOL),
                        f"actual={actual:.17g}, expected={expected:.17g}, "
                        f"atol={atol}, rtol={REL_TOL}")

    def test_first_order_smooth_flight(self):
        """Compare four endpoint errors at one exactly shared physical time.

        Constant acceleration (0,-g), without contacts or drag, integrates to
        x=x0+vx0*t, y=y0+vy0*t-g*t*t/2, vx=vx0, vy=vy0-g*t.
        Summing v_y,k=vy0-k*g*h yields
        y_N=y0+N*h*vy0-g*h*h*N*(N+1)/2. With T=N*h, the signed error is
        -g*T*h/2, hence E(h)/E(h/2)=2 and log2(ratio)=1.
        The order uses abs(numerical_y-exact_y), WITHOUT bias subtraction.
        Horizontal position and both velocities are separate roundoff checks.
        """
        x0, y0, vx0, vy0, g, duration = 10.0, 20.0, 1.3, 2.7, 9.81, 1.5
        exact_x = x0 + vx0 * duration
        exact_y = y0 + vy0 * duration - 0.5 * g * duration**2
        exact_vy = vy0 - g * duration
        # Binary-exact h and T; integer N is specified, not rounded from T/h.
        levels = ((1/16, 24), (1/32, 48), (1/64, 96), (1/128, 192))
        for advance in (step, complete_step):
            with self.subTest(entry=advance.__name__):
                errors = []
                for h, count in levels:
                    with self.subTest(h=h, steps=count):
                        self.assertEqual(count * h, duration)
                        p = PhysicsParameters(gravity=g, dt=h)
                        box = Box(width=100.0, height=100.0)
                        s = CircleState(x=x0, y=y0, vx=vx0, vy=vy0)
                        for n in range(1, count + 1):
                            if advance is complete_step:
                                self.assertEqual(advance(s, p, box), [])
                            else:
                                advance(s, p)
                            self.assertEqual(s.step_count, n)
                            # Also checks that contact-free step is used in a
                            # geometrically valid region; no resolver is called.
                            self.assertGreater(s.x, p.radius + 1.0)
                            self.assertLess(s.x, box.width - p.radius - 1.0)
                            self.assertGreater(s.y, p.radius + 1.0)
                            self.assertLess(s.y, box.height - p.radius - 1.0)
                        self.assertEqual(s.step_count * h, duration)
                        self.close(s.x, exact_x, POSITION_ATOL)
                        self.close(s.vx, vx0, VELOCITY_ATOL)
                        self.close(s.vy, exact_vy, VELOCITY_ATOL)

                        signed_error = s.y - exact_y
                        error = abs(signed_error)
                        self.assertTrue(math.isfinite(error))
                        self.assertGreater(error, 1_000_000 * POSITION_ATOL)
                        ratio = errors[-1] / error if errors else None
                        order = math.log2(ratio) if ratio is not None else None
                        comparison = ("ratio=-- q=--" if ratio is None else
                                      f"ratio={ratio:.15g} q={order:.15g}")
                        print(f"{advance.__name__}: h={h:.10g} s N={count} "
                              f"T={count*h:g} s signed_error={signed_error:.15g} m "
                              f"error={error:.15g} m {comparison}", flush=True)
                        if errors:
                            self.assertLess(error, errors[-1])
                            self.assertAlmostEqual(order, 1.0, delta=ORDER_ATOL)
                        # Additional sign/bias check; never correct y before
                        # measuring the error or estimating convergence order.
                        self.assertLess(signed_error, 0.0)
                        self.close(signed_error, -0.5*g*duration*h, POSITION_ATOL)
                        errors.append(error)
                self.assertEqual(len(errors), 4, "all refinement levels must pass")


if __name__ == "__main__":
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
