"""Independent analytical references for translational motion (unittest).

From the repository root (tested with Python 3.12.10):
python -B -m hw4.check_analytical
Module execution keeps the root simulator modules importable.
No simulator reference/energy/time helpers are used to generate expected values.
See assign3/SPEC.md [EQ-MOTION], [EQ-FLIGHT], [EQ-STEP], [EQ-NORMAL].
"""

import math
import sys
import unittest

from integration import complete_step, step
from state import Box, CircleState, PhysicsParameters


# For <=200 steps and positions/speeds below 9 SI units, a conservative
# 8*N*epsilon*scale roundoff estimate is <3.2e-12. Allow 1e-11 in each
# quantity's SI unit, plus a 1e-13 relative allowance at nonzero scales.
# math.isclose uses max(atol, rtol*max(|actual|, |expected|)); absolute
# tolerance controls near-zero values, including vy at the apex. These
# allowances are NOT tolerances for the O(h) Euler height error.
ABS_TOL = 1e-11
REL_TOL = 1e-13


class AnalyticalChecks(unittest.TestCase):
    """Check full trajectories against independently integrated equations."""

    def close(self, actual, expected):
        """Compare finite scalars in the same SI unit with explicit tolerances."""
        self.assertTrue(math.isfinite(actual))
        self.assertTrue(math.isclose(actual, expected,
                                     abs_tol=ABS_TOL, rel_tol=REL_TOL),
                        f"actual={actual:.17g}, expected={expected:.17g}, "
                        f"atol={ABS_TOL}, rtol={REL_TOL}")

    def test_upward_launch_through_apex(self):
        """Check ascent, zero vertical speed, descent, and signed Euler bias.

        Assumptions: constant gravity, no contacts or drag, fixed h, SI units.
        Integrating dv/dt=(0,-g) and dx/dt=v gives
        x=8-1.25*t, vy=4.905-9.81*t, y=3+4.905*t-9.81*t*t/2.
        Thus t_apex=0.5, y_apex=4.22625; at t=1, x=6.75, y=3,
        vy=-4.905. Summing velocities v_y,k=v_y,0-k*g*h gives
        y_n=y0+n*h*vy0-g*h*h*n*(n+1)/2, hence y_n-y(t)=-g*h*t/2.
        At t=1, discrete y is 2.95095 (h=.01), 2.975475 (h=.005).
        Both paths stay well inside Box(20,20), even with this height bias.
        Different masses must give identical motion since F_y=-m*g.
        """
        for advance in (step, complete_step):
            for count, endpoint_y in ((100, 2.95095), (200, 2.975475)):
                for mass in (0.25, 7.0):
                    with self.subTest(entry=advance.__name__, steps=count,
                                      mass=mass):
                        h = 1.0 / count
                        p = PhysicsParameters(gravity=9.81, dt=h, mass=mass)
                        s = CircleState(x=8.0, y=3.0, vx=-1.25, vy=4.905)
                        box = Box(width=20.0, height=20.0)
                        max_residual = 0.0
                        for n in range(1, count + 1):
                            if advance is complete_step:
                                self.assertEqual(advance(s, p, box), [])
                            else:
                                advance(s, p)
                            # Independent loop time: do not use s.time(p).
                            t = n * h
                            exact_y = 3.0 + 4.905*t - 0.5*9.81*t*t
                            bias = -0.5*9.81*h*t
                            self.close(s.x, 8.0 - 1.25*t)
                            self.close(s.vx, -1.25)
                            self.close(s.vy, 4.905 - 9.81*t)
                            self.close(s.y - exact_y, bias)
                            self.assertEqual(s.step_count, n)
                            max_residual = max(max_residual,
                                               abs(s.y - exact_y - bias))
                            if n == count // 2:
                                self.close(s.vy, 0.0)
                                self.close(s.x, 7.375)
                                self.close(s.y, 4.22625 - 0.25*9.81*h)
                        self.close(s.x, 6.75)
                        self.close(s.y, endpoint_y)
                        self.close(s.vy, -4.905)
                        print(f"launch {advance.__name__}, h={h}, m={mass}: "
                              f"y={s.y:.12g}, expected={endpoint_y}; "
                              f"max height-bias residual={max_residual:.3g} m")

    def test_aligned_elastic_wall_reflection(self):
        """Check an exact piecewise-linear trajectory through one impact.

        With g=0, e=1, radius .25 and W=4, the right center boundary is
        3.75 m. Starting at x=1 with vx=2 gives impact time (3.75-1)/2
        =1.375 s. For t<1.375: x=1+2*t, vx=2. At and after impact,
        use the post-impact convention: x=3.75-2*(t-1.375), vx=-2.
        The tangent follows y=2+.5*t, vy=.5 throughout. Thus at 2 s,
        (x,y,vx,vy)=(2.5,3,-2,.5). Steps 1/16 and 1/32 align impact
        exactly (steps 22 and 44); all inputs/increments are binary exact.
        There is no integration or impact-time truncation error in this case.
        """
        for rate in (16, 32):
            with self.subTest(rate=rate):
                p = PhysicsParameters(gravity=0.0, restitution=1.0,
                                      radius=0.25, dt=1.0/rate)
                s = CircleState(x=1.0, y=2.0, vx=2.0, vy=0.5)
                box = Box(width=4.0, height=5.0)
                for n in range(1, 2*rate + 1):
                    records = complete_step(s, p, box)
                    t = n / rate
                    before = t < 1.375
                    self.close(s.x, 1.0+2.0*t if before
                               else 3.75-2.0*(t-1.375))
                    self.close(s.vx, 2.0 if before else -2.0)
                    self.close(s.y, 2.0+0.5*t)
                    self.close(s.vy, 0.5)
                    self.assertEqual(s.step_count, n)
                    if n == 11*rate // 8:
                        self.assertEqual(len(records), 1)
                        record = records[0]
                        self.assertEqual(record.surface, "right")
                        self.close(record.normal_velocity_before, -2.0)
                        self.close(record.normal_velocity_after, 2.0)
                        self.assertEqual(record.position_correction, (0.0, 0.0))
                        self.assertTrue(record.is_impact)
                    else:
                        self.assertEqual(records, [])
                self.close(s.x, 2.5)
                self.close(s.y, 3.0)
                print(f"elastic reflection h=1/{rate}: "
                      f"(x,y,vx,vy)={(s.x, s.y, s.vx, s.vy)}; "
                      "expected=(2.5, 3, -2, 0.5)")


if __name__ == "__main__":
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
