"""Independent momentum, kinetic-energy, and collision energy-balance tests.

From the repository root: python -B -m hw4.check_conservation
SI units; no gravity in trajectory tests, no friction, fixed immovable walls.
No particle momentum conservation is asserted across wall impacts.
"""

from dataclasses import replace
import math
import sys
import unittest

from integration import complete_step
from state import Box, CircleState, PhysicsParameters


# Each comparison recomputes p or K from state, without summing over time.
# At g=0 velocities are copied or sign-reversed (e=1), so 1024 steps do not
# accumulate velocity roundoff. Position error cannot change K. For the few
# products/sums in p, K and single-impact loss, 32*epsilon ~= 7.1e-15 bounds
# ordinary roundoff at these scales; rtol=1e-13 gives margin. atol=1e-12 in
# J, kg*m/s, or m/s handles cancellation/near zero. No Euler drift allowance.
ABS_TOL = 1e-12
REL_TOL = 1e-13


def momentum(state, mass):
    """Independent test reference in kg*m/s; no production helper call."""
    return mass * state.vx, mass * state.vy


def kinetic_energy(state, mass):
    """Independent test reference in joules; no production helper call."""
    return mass * (state.vx * state.vx + state.vy * state.vy) / 2.0


class ConservationChecks(unittest.TestCase):
    """Check conservation where applicable, and loss where restitution acts."""

    def close(self, actual, expected):
        self.assertTrue(math.isfinite(actual) and math.isfinite(expected))
        self.assertTrue(math.isclose(actual, expected, abs_tol=ABS_TOL,
                                     rel_tol=REL_TOL),
                        f"actual={actual:.17g}, expected={expected:.17g}; "
                        f"atol={ABS_TOL}, rtol={REL_TOL}")

    def check_impact(self, before, after, record, restitution):
        """Use actual state components, not records, as the physics oracle."""
        normal, tangent, sign = {
            "floor": ("vy", "vx", 1),
            "left": ("vx", "vy", 1),
            "right": ("vx", "vy", -1),
        }[record.surface]
        vn_before = sign * getattr(before, normal)
        vn_after = sign * getattr(after, normal)
        self.assertLess(vn_before, 0.0)
        self.assertGreater(vn_after, 0.0)
        self.assertTrue(record.is_impact)
        self.close(vn_after, -restitution * vn_before)
        self.close(getattr(after, tangent), getattr(before, tangent))
        self.close(record.normal_velocity_before, vn_before)
        self.close(record.normal_velocity_after, vn_after)
        return vn_before

    def test_gravity_free_flight_momentum_and_energy(self):
        """No force/contact: nonzero vector momentum and K stay constant."""
        for mass in (0.25, 2.5, 1000.0):
            with self.subTest(mass=mass):
                p = PhysicsParameters(gravity=0.0, mass=mass, dt=1/128)
                s = CircleState(x=50.0, y=50.0, vx=1.7, vy=-0.9)
                box = Box(width=100.0, height=100.0)
                initial_p = momentum(s, mass)
                initial_k = kinetic_energy(s, mass)
                self.assertTrue(all(value != 0 for value in initial_p))
                self.assertGreater(initial_k, 0)
                max_dp = max_dk = 0.0
                for n in range(1, 1025):
                    self.assertEqual(complete_step(s, p, box), [])
                    self.assertEqual(s.step_count, n)
                    for actual, expected in zip(momentum(s, mass), initial_p):
                        self.close(actual, expected)
                        max_dp = max(max_dp, abs(actual - expected))
                    k = kinetic_energy(s, mass)
                    self.close(k, initial_k)
                    max_dk = max(max_dk, abs(k - initial_k))
                print(f"free flight m={mass}: p0={initial_p}, K0={initial_k:g} J; "
                      f"max momentum drift={max_dp:g}, max K drift={max_dk:g} J")

    def test_repeated_elastic_collisions(self):
        """Conserve K through a floor impact and repeated left/right impacts.

        Two independent launches exercise both horizontal directions. With no
        gravity/ceiling the floor cannot be revisited in a single trajectory.
        Isolated impacts let full pre/post state establish tangent preservation;
        simultaneous corner impacts are deliberately excluded and asserted absent.
        """
        for vx in (-2.3, 2.3):
            with self.subTest(vx=vx):
                p = PhysicsParameters(gravity=0.0, restitution=1.0,
                                      mass=2.5, dt=1/64)
                s = CircleState(x=2.0, y=1.5, vx=vx, vy=-1.1)
                box = Box(width=4.0, height=30.0)
                initial_k = kinetic_energy(s, p.mass)
                counts = dict(floor=0, left=0, right=0)
                max_dk = 0.0
                for n in range(1, 1025):
                    before = replace(s)
                    records = complete_step(s, p, box)
                    self.assertEqual(s.step_count, n)
                    self.assertLessEqual(len(records), 1, "isolated impacts required")
                    k = kinetic_energy(s, p.mass)
                    self.close(k, initial_k)
                    max_dk = max(max_dk, abs(k - initial_k))
                    for record in records:
                        self.check_impact(before, s, record, 1.0)
                        self.close(k, kinetic_energy(before, p.mass))
                        counts[record.surface] += 1
                self.assertEqual(counts["floor"], 1)
                self.assertGreaterEqual(counts["left"], 4)
                self.assertGreaterEqual(counts["right"], 4)
                print(f"elastic vx0={vx}: impacts={counts}, "
                      f"K0={initial_k:g} J, max K drift={max_dk:g} J")

    def test_inelastic_collision_energy_balance(self):
        """Energy balance, not conservation: Delta K=-m*(1-e^2)*vn^2/2.

        Decompose K=m*(vn^2+vt^2)/2. Tangent preservation cancels vt^2;
        vn_after=-e*vn_before gives the stated loss. Each g=0 complete step
        crosses exactly one boundary, with |vn|=2.3 and |vt|=1.1 m/s.
        """
        cases = (
            ("floor", dict(x=2.0, y=0.3, vx=1.1, vy=-2.3), "vy", 1),
            ("left", dict(x=0.3, y=2.0, vx=-2.3, vy=1.1), "vx", 1),
            ("right", dict(x=3.7, y=2.0, vx=2.3, vy=1.1), "vx", -1),
        )
        for e in (0.3, 0.8):
            for surface, fields, normal, sign in cases:
                with self.subTest(e=e, surface=surface):
                    p = PhysicsParameters(gravity=0.0, restitution=e,
                                          mass=2.5, dt=0.1)
                    s = CircleState(**fields)
                    before = replace(s)
                    k_before = kinetic_energy(before, p.mass)
                    vn_before = sign * getattr(before, normal)
                    expected_loss = -0.5*p.mass*(1-e*e)*vn_before*vn_before
                    records = complete_step(s, p, Box())
                    self.assertEqual([r.surface for r in records], [surface])
                    self.check_impact(before, s, records[0], e)
                    k_after = kinetic_energy(s, p.mass)
                    self.close(k_after - k_before, expected_loss)
                    # Loss is several joules: strict non-increase needs no slack.
                    self.assertLess(k_after, k_before)
                    print(f"inelastic {surface}, e={e}: dK={k_after-k_before:.12g} J, "
                          f"expected={expected_loss:.12g} J, "
                          f"residual={k_after-k_before-expected_loss:.3g} J")

    def test_energy_helper_against_independent_values(self):
        """Check the production E=K+m*g*y helper separately, without stepping."""
        from validation import energy

        # Hand values: m=2.5, speed^2=25 -> K=31.25 J;
        # m*g*y=49.05 J at g=9.81, y=2. No conservation claim under gravity.
        for gravity, y, vx, vy, expected in (
            (0.0, 2.0, -3.0, 4.0, 31.25),
            (9.81, 2.0, -3.0, 4.0, 80.3),
            (9.81, 2.0, 0.0, 0.0, 49.05),
            (9.81, 0.0, 0.0, 0.0, 0.0),
        ):
            with self.subTest(gravity=gravity, y=y, vx=vx, vy=vy):
                s = CircleState(y=y, vx=vx, vy=vy)
                p = PhysicsParameters(mass=2.5, gravity=gravity)
                reference = kinetic_energy(s, p.mass) + p.mass*gravity*y
                self.close(reference, expected)
                self.close(energy(s, p), expected)
        print("energy helper: 4 independent static values passed")


if __name__ == "__main__":
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
