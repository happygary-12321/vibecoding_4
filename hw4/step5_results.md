# Part 5: limiting-case testing results

This is an explicitly agent-generated factual report, not the user's personal
testing log. Earlier reports remain unchanged as historical records.

## Inspection and assumptions

Reviewed SPEC's supported parameters, motion/update equations and contact rules;
the state, integration and contact implementation; existing integration/contact
tests; HW4 Parts 1–4 tests, reports, and README. SPEC allows zero gravity and
restitution endpoints, but requires positive timestep, mass, and radius. All
new fixtures respect these ranges and use fresh independent states.

Physics is 2D translation in SI units, with +y upward, fixed floor and side
walls, and no friction or rotation. All Part 5 cases set gravity to zero.
Every fixture explicitly specifies radius, mass, restitution, timestep, box
width and height. Independent formulas and literal hand-derived values are
used; production reference, time, and energy helpers are not used as oracles.
No new resting-contact model or energy-conservation requirement under gravity
is introduced.

## Independent references and rationale

### Zero gravity with nonzero velocity

With `dv/dt=0`, integration gives `x=x0+vx0*t`, `y=y0+vy0*t`, with constant
velocity. Initial state is `(12.3,8.4,-1.7,2.3)` in SI units, r=0.25 m,
m=2.5 kg, e=0.6, h=0.01 s, and box `(30,30)` m. Each API (`step` and
`complete_step`) runs 300 steps/3 s. The exact endpoint is `(7.2,15.3)` m.

Every step checks both positions against the independently integrated formula,
both velocities, step count, and geometric clearance. Complete steps must
return no contacts. Loop index times 0.01 supplies reference time, never the
production time helper. Unlike earlier conservation checks, this test would
fail if velocities were preserved but positions failed to advance correctly.

### Zero gravity and zero velocity

Initial state `(2.13,1.37,0,0)` lies strictly inside a `(6,5)` m box with
r=0.25 m, m=2.5 kg, e=0.6, h=0.01 s. Both APIs run 200 steps/2 s.
The exact solution is constant position and zero velocity. Finite stored
values plus zero are exactly unchanged, so state components use exact equality,
as do advancing step counts. Complete steps must return empty contact lists.

### Zero restitution at each surface

Use g=0, e=0, r=0.25 m, m=2.5 kg, h=0.1 s, box `(6,5)` m. Independent
single-surface fixtures are:

| Surface | Initial (x,y) m | Initial (vx,vy) m/s | Normal boundary | Expected first correction (m) |
| --- | --- | --- | --- | --- |
| Floor | (2,0.4) | (0.7,-3.2) | y=0.25 | (0,0.17) |
| Left | (0.4,2) | (-3.2,0.7) | x=0.25 | (0.17,0) |
| Right | (5.6,2) | (3.2,0.7) | x=5.75 | (-0.17,0) |

Each first step crosses one boundary with finite penetration. Normal velocity
before impact is -3.2 m/s in the inward-normal convention. Restitution gives
`vn_after=-e*vn_before=0`; the 0.7 m/s tangent is unchanged. Decomposing K into
normal and tangent components gives:

```text
K_before = 0.5*2.5*(3.2^2+0.7^2) = 13.4125 J
K_after  = 0.5*2.5*0.7^2 = 0.6125 J
K_after-K_before = -0.5*m*vn_before^2 = -12.8 J
```

Each impact is followed by 20 more complete steps. The normal coordinate must
remain exactly at its assigned boundary and normal velocity exactly zero;
these checks disallow rebound or penetration. Tangential velocity remains
0.7 m/s and tangential position follows `2+0.7*n*0.1`, reaching 3.47 m at
step 21. This stays away from unintended surfaces and corners.

SPEC detects exact touching with inclusive inequalities. Thus every follow-up
step must still report the same surface, but with zero correction, zero normal
velocities, and `is_impact=False`. This tests the current algorithm rather than
assuming empty lists or adding a new contact model. Each first record must
instead be an impact. The test has its own zero-speed assertions and does not
reuse Part 2's helper requiring positive outgoing velocity.

### Approach to zero restitution

Five fresh floor-impact runs use the identical pre-impact conditions above,
varying only e through 0.5, 0.1, 0.01, 0.001, and 0. The position is projected
to y=0.25 in every case. From restitution and normal kinetic energy:

```text
outgoing speed = e*abs(vn_before) = 3.2*e
remaining normal K = 0.5*m*e^2*vn_before^2 = 12.8*e^2
```

Both quantities must decrease strictly through the sequence, remain strictly
positive for positive e, and equal zero at e=0. Tangential velocity is checked
separately. Normal energy is computed directly from the measured normal
velocity, not by subtracting nearly equal total and tangential energies.

## Tolerance rationale

Ordinary floating comparisons use `math.isclose`, with finite operands and
relative tolerance 1e-13. Position absolute tolerance is 2e-11 m; velocity
absolute tolerance is 1e-13 m/s; ordinary energy absolute tolerance is 1e-12 J.
The acceptance bound is `max(atol,rtol*max(abs(actual),abs(expected)))`.

- Position: at most 300 additions and coordinate scales below 30 m give a
  conservative `8*N*epsilon*30 < 1.6e-11 m` roundoff estimate, using binary64
  epsilon about 2.22e-16. The 2e-11 allowance includes formula evaluation and
  cancellation. No truncation error is present for constant velocity.
- Velocity: no force accumulation occurs; components are preserved or subjected
  to one restitution multiplication. A 1e-13 absolute/relative allowance is
  comfortably above a few ulps at speeds up to 3.2 m/s.
- Energy: a few products and a subtraction at a 14 J scale incur roundoff on
  the order of tens of epsilon times that scale, below 1e-12 J. This tolerance
  checks an energy balance, not conservation of the pre-impact energy.
- Positive small-e speed and normal energy: absolute tolerance is **zero** and
  relative tolerance is **1e-12**, plus explicit positivity assertions. Even at
  e=0.001, expected speed is 0.0032 m/s and normal K is 1.28e-5 J. Effective
  allowances are approximately 3.2e-15 m/s and 1.28e-17 J. A zeroed response
  therefore cannot pass. The formulas involve only a few multiplications, so
  their relative roundoff is far smaller than 1e-12.
- Exact checks: step counts, contact identities, impact flags, stationary states,
  assigned normal boundary positions, e=0 normal velocities, and follow-up zero
  corrections use equality. These are stored assignments or arithmetic with
  zero; no small positive-e response is subjected to an absolute-zero shortcut.

Tolerances were selected before execution and never loosened.

## Measured results

Standalone and combined runs agreed.

| Case | Measurements |
| --- | --- |
| Uniform motion, both APIs | Endpoint (7.2,15.3) m; maximum x residual 1.3589129821411916e-13 m; y residual 9.414691248821327e-14 m; velocity residuals zero; no contacts |
| Stationary interior, both APIs | Position/velocity residuals zero, count=200, no contacts |
| Each e=0 surface | Normal velocity zero, K_after=0.6125 J, Delta K=-12.8 J; 21 contacts consisting of one impact and 20 non-impact touches |
| e=0 follow-up tangent | Maximum position residual 3.552713678800501e-15 m; velocity residual zero |
| e=0 energy balance | Maximum loss residual 1.7763568394002505e-15 J; remaining-K residual 1.1102230246251565e-16 J |
| First corrections | Maximum residual 2.7755575615628914e-17 m at floor/left, 8.326672684688674e-17 m at right |

Measured approach to zero restitution:

| e | Outgoing speed (m/s) | Remaining normal K (J) | Speed residual (m/s) | Normal-K residual (J) |
| --- | --- | --- | --- | --- |
| 0.5 | 1.6 | 3.2 | 0 | 0 |
| 0.1 | 0.32 | 0.128 | 0 | +2.78e-17 |
| 0.01 | 0.032 | 0.00128 | 0 | 0 |
| 0.001 | 0.0032 | 0.0000128 | 0 | -1.69e-21 |
| 0 | 0 | 0 | 0 | 0 |

No rebound, penetration, unintended contact, or tangential damping occurred
in the e=0 follow-up cases. All monotonicity and positivity assertions passed.

## Commands and actual verification

Working directory: `D:\CodexCLI\vibecoding\HW3_submission`.
Interpreter: CPython 3.12.10, MSC v.1943, 64-bit Windows AMD64. No other
version was tested; HW4 imposes no exact patch-version guard.
The installed interpreter was accessed with sandbox approval:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.check_limiting
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v hw4.check_analytical hw4.check_conservation hw4.check_convergence hw4.check_symmetry hw4.check_limiting
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v check_integration check_contacts check_scheduling check_cli
```

| Run | Actual result | Reported unittest runtime | Exit code |
| --- | --- | --- | --- |
| Part 5 alone | 4 test methods passed, 12 parameter/API subcases | 0.005 s | 0 |
| Parts 1–5 together | 14 test methods passed | 0.081 s | 0 |
| Existing regression suite | 26 test methods passed | 5.125 s | 0 |

The 12 Part 5 subcases comprise two uniform-flight APIs, two stationary APIs,
three e=0 surfaces, and five approach-to-zero values. They are not additional
unittest method counts. Existing CLI tests included temporary headless figure
generation; no GUI or overwrite of saved figure evidence occurred.

## Initial failures, fixes, and changed files

No initial test failures occurred. No implementation fixes, fixture changes,
or tolerance adjustments were needed. Physical requirements were unchanged.

- New `hw4/check_limiting.py`: independent limiting-case tests.
- New `hw4/step5_results.md`: this explicitly agent-generated report.
- Updated `hw4/README.md` and root README: Part 5 scope, links, and commands.

Earlier tests/reports, simulator source, and SPEC are unchanged. No intentional
bugs were introduced, no unsupported zero timestep/mass/radius was tested, and
no commit was made. Finite positive-e samples support the stated limit for the
selected collision; they do not test underflow-scale restitution or introduce
a resting model under nonzero gravity.

## Remaining assignment work

Parts 1–5 now have implemented and passing physics tests. This does not by
itself certify that the entire assignment is complete. The remaining items
identified in the user's instructions are:

1. **Major-function coverage audit.** Map each major simulator function to
   meaningful tests and document any gaps, then add justified missing tests.
   Current HW4 tests exercise `step`, `complete_step`, contact resolution via
   complete steps, state construction, and the energy helper. Legacy tests
   additionally cover validation, scheduler, CLI, and mocked dispatch, but no
   comprehensive HW4 coverage inventory or measured coverage claim has been
   produced. GUI behavior is not verified by these headless checks. Confirm
   any rubric-specific coverage scope before declaring this requirement met.
2. **Intentional-bug experiment.** Still pending for HW4, and explicitly not
   authorized in this step. After review/authorization, isolate a deliberate
   defect, record which tests fail and why, restore the correct implementation,
   and verify the restored suite. Historical Assignment 2 defect materials do
   not substitute for a newly documented HW4 experiment.
3. **Personally written log with transcript references.** The user must write
   their own log, citing identifiable transcript exchanges and test evidence.
   These reports provide factual inputs, not a personal narrative. Preserve
   or export the relevant HW4 transcript and establish usable references;
   existing historical transcript files do not establish coverage of this
   current session. No personal log or current HW4 transcript export was made.
4. **Git commits.** Still pending explicit review/authorization. Review the HW4
   files and README changes, stage only the intended scope, and make the
   assignment-required commits with accurate messages/evidence. No commit was
   made in Parts 1–5; no required commit count or structure is inferred here.

A complete HW4 assignment handout was not found in the inspected files; the
list above tracks the requirements expressly identified in this conversation,
not a claim that every external submission/rubric detail has been audited.
