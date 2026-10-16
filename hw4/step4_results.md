# Part 4: symmetry and invariance results

This is an explicitly agent-generated factual report, not the user's personal
testing log. Parts 1–3 reports remain unchanged as historical records.

## Inspection and model

Reviewed SPEC's governing equations, coordinate conventions, integration order,
and contact rules; `integration.py`, `contacts.py`, and `state.py`; existing
integration/contact tests and HW4 tests; the Part 1–3 reports and READMEs.
The model has a translating circle, constant vertical gravitational acceleration,
fixed walls, and frictionless normal restitution. There is no rotational state.
Tests use standard-library unittest and fresh independent mutable states.

## Horizontal reflection derivation

For a fixed box width W, define in test code:

```text
R(x,y,vx,vy) = (W-x, y, -vx, vy)
```

Gravity `(0,-g)` is unchanged. Under the velocity-first update, mirrored x
advances as `(W-x)+(-vx)*h = W-(x+vx*h)`, and both vertical updates are
identical. Thus reflection commutes with the discrete integration step in
exact arithmetic. The floor and radius offset are unchanged; left `x<=r`
maps to right `x'>=W-r`. Both walls use the same restitution, so the
corresponding normal responses also commute with reflection.

At initialization and after every step, the tests independently assert:

```text
x_A+x_B=W; y_A=y_B; vx_A=-vx_B; vy_A=vy_B
step_count_A=step_count_B
```

No production reference helper constructs these expected relations. Each state
is advanced independently through the production integrator.

### Contact records

With reflection matrix `S=diag(-1,1)`, velocity transforms as `v'=S*v`.
Normals into the allowed region are floor `(0,1)`, left `(1,0)`, right `(-1,0)`.
They transform as `n'=S*n`, so `vn'=n' dot v'=n dot v`. Consequently both
before and after scalar normal velocities are unchanged by reflection, even
though the horizontal Cartesian velocity reverses. Position corrections are
vectors, so `(dx,dy)'=(-dx,dy)`. Impact flags are unchanged.

Records are indexed by surface and checked for duplicate identities. Exact
surface-set comparisons use floor-to-floor and left-to-right/right-to-left
mapping; no list-order assumption is made. Normal velocities and correction
components are compared using numerical tolerances, while impact flags and
contact identities are exact. Contact sequences agree step by step under the
mapping, not just in aggregate counts.

## Mass invariance derivation

The model's acceleration is `-g`, independent of mass (equivalently F=-m*g
divided by m). Integration, radius-based position projection, and fixed-wall
restitution contain no mass dependence. Therefore identical initial states
with identical gravity, radius, restitution, timestep, and box geometry have
identical position/velocity/count/contact trajectories for any positive masses.

Tests compare 0.125 kg and 128 kg, a factor of 1024, using independently
constructed states and parameter objects. Contact sequences and records use
the identity mapping in this case. Momentum and kinetic/potential energy scale
with mass and are explicitly not asserted invariant.

## Fixtures and safeguards

All parameters are explicitly specified, including radius, mass, restitution,
gravity, timestep, box width/height, and initial step count zero.

| Fixture | Parameters and trajectory |
| --- | --- |
| Contact-free reflection | W=40 m, H=40 m, r=0.23 m, m=2.5 kg, g=9.81 m/s^2, e=0.8, h=0.01 s; A starts `(7.13,20.17,1.37,2.41)`; B is its reflection. 100 steps/1 s for each of `step` and `complete_step`. |
| Colliding reflection | W=4.6 m, H=12 m, r=0.23 m, m=0.125 kg, g=9.81 m/s^2, h=0.01 s; A starts `(1.17,3.17,3.13,0.41)`; B is its reflection. 400 steps/4 s, separately at e=1 and e=0.8. |
| Mass invariance | Same colliding fixture, but A and B have identical initial states and masses 0.125 and 128 kg. 400 steps/4 s, separately at e=1 and e=0.8. |

The contact-free test checks geometric clearance at every step for both APIs,
and asserts empty contact lists for `complete_step`. Its analytical endpoint
has A's x=8.5 m and y=17.675 m (the discrete y is 17.62595 m),
well away from boundaries. Both initial velocities and gravity are nonzero.

For collision fixtures, the independent pre-contact endpoint expressions
`x+vx*h` and `y+(vy-g*h)*h` assess distance to x=r, x=W-r, and y=r before
each step. Every distance must exceed 1e-6 m. This is a fixture guard, not a
tolerance allowing mismatched contacts. The observed minimum was 0.0074 m
in every collision pair. Numerical contact identities must still agree exactly
on each step. At most one contact is permitted per state per step, ruling out
simultaneous corners. Every run must have actual impacts on floor, left, and
right, so a contact-free or stalled run cannot pass by symmetry alone.

The chosen crossing increments produce clear penetration on collision steps
instead of relying on exact touching. Fixtures passed these guards on the first
execution; no changes to contact rules, assertions, or fixture values were needed.

## Tolerance rationale

Floating comparisons use `math.isclose` with absolute tolerance 5e-10 in the
quantity's unit (m or m/s) and relative tolerance 1e-13. The acceptance bound
is `max(atol,rtol*max(abs(actual),abs(expected)))`; both values must be finite.
Residuals are reported per state and contact component.

These runs have at most 400 steps, duration at most 4 s, and arithmetic scales
below 50 in SI units. A conservative paired arithmetic estimate is
`16*N*epsilon*50*(1+T) < 3.6e-10`, using binary64 epsilon about 2.22e-16.
The factor includes both trajectories, several per-step operations, and
propagation of velocity roundoff into position over the finite interval. The
5e-10 absolute budget leaves margin; the relative term is at most 5e-12 at
these scales, so absolute tolerance controls these fixtures.

This estimate assumes the same contact branches; that assumption is separately
verified by exact stepwise identity checks and the threshold-margin guard.
Projection resets contact coordinates, and e<=1 does not amplify normal-velocity
differences when the same branches occur. This is a roundoff allowance for
symmetry comparisons, not a bound on discretization error against continuous
motion. Mass is absent from the update, so mass comparisons actually measured
zero residual. Counts, expected step indices, contact identities, and impact
flags use exact equality. The 1e-6 m fixture margin exceeds the numerical
absolute allowance by 2000; observed threshold separation is much larger still.
All tolerances were chosen before execution and never loosened.

## Measured residuals and contacts

Standalone and combined runs produced the same measurements.

| Pair | Max x symmetry residual (m) | Max correction-x residual (m) | Other numerical residuals |
| --- | --- | --- | --- |
| Contact-free, `step` | 0 | Not applicable | All 0 |
| Contact-free, `complete_step` | 0 | Not applicable | All 0 |
| Colliding reflection, e=1 | 8.881784197001252e-15 | 3.3584246494910985e-15 | All 0 |
| Colliding reflection, e=0.8 | 8.881784197001252e-15 | 3.3584246494910985e-15 | All 0 |
| Mass invariance, e=1 | 0 | 0 | All 0 |
| Mass invariance, e=0.8 | 0 | 0 | All 0 |

For reflection, x residual is `abs(x_A+x_B-W)`; for mass invariance it is
`abs(x_B-x_A)`. Other residuals cover y, vx, vy, normal velocity before/after,
and vertical correction. All count and contact-identity comparisons passed.

Every contact in the collision fixtures was an impact; contact and impact
counts therefore coincide. Tuples below are `(floor,left,right)`:

| Pair | A counts | B counts |
| --- | --- | --- |
| Contact-free, either API | (0,0,0) | (0,0,0) |
| Colliding reflection, e=1 | (3,1,2) | (3,2,1) |
| Colliding reflection, e=0.8 | (4,1,1) | (4,1,1) |
| Mass invariance, e=1 | (3,1,2) | (3,1,2) |
| Mass invariance, e=0.8 | (4,1,1) | (4,1,1) |

## Actual verification commands and results

Working directory: `D:\CodexCLI\vibecoding\HW3_submission`.
Interpreter: CPython 3.12.10, MSC v.1943, 64-bit Windows AMD64. The HW4
script has no exact patch-version restriction. No other version was tested.
Commands ran with sandbox approval for the installed interpreter:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.check_symmetry
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v hw4.check_analytical hw4.check_conservation hw4.check_convergence hw4.check_symmetry
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v check_integration check_contacts check_scheduling check_cli
```

| Run | Result | Reported unittest runtime | Exit code |
| --- | --- | --- | --- |
| Part 4 alone | 3 test methods passed, 6 trajectory pairs | 0.019 s | 0 |
| Parts 1–4 together | 10 test methods passed | 0.087 s | 0 |
| Existing regression suite | 26 test methods passed | 5.583 s | 0 |

The existing CLI suite ran its headless figure test in a temporary directory.
No GUI was launched or saved figure evidence overwritten.

## Initial failures, fixes, and changed files

No initial failures occurred. No fixture, test tolerance, implementation, or
physical-requirement changes were needed to obtain a pass.

- New `hw4/check_symmetry.py`: reflection and mass-invariance tests.
- New `hw4/step4_results.md`: this agent-generated report.
- Updated `hw4/README.md` and root README: scope, report links, and commands
  for Part 4 alone and Parts 1–4 together.

Simulator source, SPEC, prior tests, and Parts 1–3 reports are unchanged.
No intentional bugs or commits were introduced.

## Limitations

These tests establish the stated relations for the selected finite trajectories,
including isolated elastic and inelastic impacts. They do not assert symmetry
at floating-point-ambiguous touching events or cover simultaneous corners.
Symmetry tests alone cannot detect errors shared symmetrically by both runs;
the independent analytical, conservation, and convergence tests remain useful.
No vertical reflection under unchanged gravity, arbitrary translation with
fixed walls, or time reversibility of dissipative collisions/semi-implicit Euler
is claimed. Momentum and energy are not mass-invariant. Matching mirrored
trajectories does not establish exact collision timing or convergence order
across impacts.
