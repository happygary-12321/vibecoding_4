"""Horizontal reflection and mass invariance, using independent trajectories.

Run from the repository root: python -B -m hw4.check_symmetry
No vertical reflection, arbitrary translation, or time reversal is asserted.
"""

from dataclasses import replace
import math
import sys
import unittest

from integration import complete_step, step
from state import Box, CircleState, PhysicsParameters


# For <=400 steps, <=4 s and scales below 50 SI, a paired roundoff estimate
# 16*N*epsilon*50*(1+T) <3.6e-10 includes velocity-to-position propagation.
# Equal contact branches are asserted; projections reset coordinates and e<=1
# does not amplify velocity errors. These are roundoff, not truncation bounds.
ABS_TOL = 5e-10  # m or m/s
REL_TOL = 1e-13
# Fixture guard only: pre-contact endpoints must avoid every detection threshold
# by >1e-6 m (2000 times ABS_TOL). This NEVER relaxes contact identity checks.
CONTACT_MARGIN = 1e-6
MIRROR_SURFACE = {"floor": "floor", "left": "right", "right": "left"}


class SymmetryChecks(unittest.TestCase):
    """Compare fresh state objects with relations independent of the simulator."""

    def compare(self, actual, expected, maxima, label):
        self.assertTrue(math.isfinite(actual) and math.isfinite(expected))
        maxima[label] = max(maxima.get(label, 0.0), abs(actual - expected))
        self.assertTrue(math.isclose(actual, expected, abs_tol=ABS_TOL,
                                     rel_tol=REL_TOL),
                        f"{label}: actual={actual:.17g}, expected={expected:.17g}")

    def compare_states(self, a, b, width, maxima, mirrored):
        # R(x,y,vx,vy)=(W-x,y,-vx,vy). In particular x_A+x_B=W.
        self.compare(a.x + b.x if mirrored else b.x,
                     width if mirrored else a.x, maxima, "x_m")
        self.compare(b.y, a.y, maxima, "y_m")
        self.compare(b.vx, -a.vx if mirrored else a.vx, maxima, "vx_m_per_s")
        self.compare(b.vy, a.vy, maxima, "vy_m_per_s")
        self.assertEqual(a.step_count, b.step_count)

    def compare_records(self, records_a, records_b, maxima, mirrored):
        # Match identities by surface, never by the resolver's list order.
        a = {r.surface: r for r in records_a}
        b = {r.surface: r for r in records_b}
        self.assertEqual(len(a), len(records_a))
        self.assertEqual(len(b), len(records_b))
        mapped = {MIRROR_SURFACE[s] if mirrored else s for s in a}
        self.assertEqual(mapped, set(b))
        for surface, ra in a.items():
            rb = b[MIRROR_SURFACE[surface] if mirrored else surface]
            # Reflection matrix S=diag(-1,1): n'=S*n and v'=S*v, so
            # n' dot v'=n dot v. Normal scalars do NOT change sign.
            self.compare(rb.normal_velocity_before, ra.normal_velocity_before,
                         maxima, "normal_before_m_per_s")
            self.compare(rb.normal_velocity_after, ra.normal_velocity_after,
                         maxima, "normal_after_m_per_s")
            # Corrections are vectors: delta'=S*delta, thus dx'=-dx, dy'=dy.
            dx, dy = ra.position_correction
            self.compare(rb.position_correction[0], -dx if mirrored else dx,
                         maxima, "correction_x_m")
            self.compare(rb.position_correction[1], dy, maxima, "correction_y_m")
            self.assertEqual(ra.is_impact, rb.is_impact)

    def precontact_margin(self, s, p, box):
        """Guard fixture robustness using the documented endpoint equations."""
        x = s.x + s.vx*p.dt
        y = s.y + (s.vy-p.gravity*p.dt)*p.dt
        margin = min(abs(x-p.radius), abs(x-(box.width-p.radius)),
                     abs(y-p.radius))
        self.assertGreater(margin, CONTACT_MARGIN,
                           "fixture too close to exact touching")
        return margin

    def test_contact_free_horizontal_reflection(self):
        """The horizontal reflection commutes with constant vertical gravity."""
        for advance in (step, complete_step):
            with self.subTest(entry=advance.__name__):
                box = Box(width=40.0, height=40.0)
                p = PhysicsParameters(gravity=9.81, radius=0.23, mass=2.5,
                                      restitution=0.8, dt=0.01)
                a = CircleState(x=7.13, y=20.17, vx=1.37, vy=2.41, step_count=0)
                b = CircleState(x=box.width-a.x, y=a.y, vx=-a.vx,
                                vy=a.vy, step_count=0)
                self.assertIsNot(a, b)
                maxima = {}
                self.compare_states(a, b, box.width, maxima, True)
                for n in range(1, 101):
                    for s in (a, b):
                        if advance is complete_step:
                            self.assertEqual(advance(s, p, box), [])
                        else:
                            advance(s, p)
                        self.assertEqual(s.step_count, n)
                        self.assertGreater(s.x, p.radius + 1)
                        self.assertLess(s.x, box.width-p.radius-1)
                        self.assertGreater(s.y, p.radius + 1)
                    self.compare_states(a, b, box.width, maxima, True)
                print(f"free reflection {advance.__name__}: max residuals={maxima}; "
                      "contacts=0 (geometric clearance checked)", flush=True)

    def collision_pair(self, e, mirrored):
        """Run four seconds with gravity, isolated contacts, and robust margins."""
        box = Box(width=4.6, height=12.0)
        pa = PhysicsParameters(gravity=9.81, radius=0.23, mass=0.125,
                               restitution=e, dt=0.01)
        pb = replace(pa, mass=pa.mass if mirrored else 128.0)
        a = CircleState(x=1.17, y=3.17, vx=3.13, vy=0.41, step_count=0)
        b = CircleState(x=box.width-a.x if mirrored else a.x, y=a.y,
                        vx=-a.vx if mirrored else a.vx, vy=a.vy, step_count=0)
        self.assertIsNot(a, b)
        maxima = {}
        counts = [dict(floor=0, left=0, right=0) for _ in range(2)]
        impacts = [dict(floor=0, left=0, right=0) for _ in range(2)]
        min_margin = float("inf")
        self.compare_states(a, b, box.width, maxima, mirrored)
        for n in range(1, 401):
            with self.subTest(step=n):
                for s, p in ((a, pa), (b, pb)):
                    min_margin = min(min_margin, self.precontact_margin(s, p, box))
                ra = complete_step(a, pa, box)
                rb = complete_step(b, pb, box)
                for s, records, totals, impact_totals in (
                    (a, ra, counts[0], impacts[0]), (b, rb, counts[1], impacts[1])
                ):
                    self.assertEqual(s.step_count, n)
                    self.assertLessEqual(len(records), 1, "no corner contacts")
                    for record in records:
                        totals[record.surface] += 1
                        if record.is_impact:
                            impact_totals[record.surface] += 1
                self.compare_states(a, b, box.width, maxima, mirrored)
                self.compare_records(ra, rb, maxima, mirrored)
        for totals in impacts:
            for surface in ("floor", "left", "right"):
                self.assertGreater(totals[surface], 0, f"missing {surface} impact")
        print(f"{'reflection' if mirrored else 'mass invariance'} e={e}: "
              f"masses=({pa.mass},{pb.mass}); max residuals={maxima}; "
              f"contacts A/B={counts}; impacts A/B={impacts}; "
              f"min pre-contact threshold distance={min_margin:.12g} m", flush=True)

    def test_colliding_horizontal_reflection(self):
        """Floor maps to floor; left and right exchange, for e=1 and e=0.8."""
        for e in (1.0, 0.8):
            with self.subTest(restitution=e):
                self.collision_pair(e, mirrored=True)

    def test_mass_invariance(self):
        """Acceleration and fixed-wall restitution are independent of mass.

        Compare masses differing by 1024, with all other parameters fixed.
        Momentum and energy scale with mass and are NOT invariance assertions.
        """
        for e in (1.0, 0.8):
            with self.subTest(restitution=e):
                self.collision_pair(e, mirrored=False)


if __name__ == "__main__":
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
