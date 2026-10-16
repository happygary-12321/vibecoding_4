# First-step analytical testing results

This is an agent-generated factual report, not the user's personal testing log.
It records the first-step findings and verification, with a separate relocation
verification below. No intentional bugs were introduced and no commit was made.

## Model and assumptions

Inspection covered `assign3/SPEC.md`, the root README, the physics implementation,
and existing tests. The simulator represents one translating 2D circle under
constant gravity. Mutable state is `(x, y, vx, vy, step_count)`; physics and box
parameters are frozen dataclasses. Positions locate the center. The origin is
the floor's left endpoint, +x points right, and +y points up. Units are meters,
seconds, kilograms, m/s, and m/s^2; restitution and step counts are dimensionless.
There is no rotation or angular state, so orientation equivalence is inapplicable.

On contact-free intervals, the governing equations are:

```text
dx/dt = vx       dy/dt = vy
dvx/dt = 0       dvy/dt = -g
F_y = -m*g
```

The numerical method is velocity-first semi-implicit Euler with fixed step h:

```text
vy <- vy - g*h
x  <- x + vx*h
y  <- y + vy*h   (updated vy)
step_count <- step_count + 1
```

Reported simulation time is `step_count*h`. Complete steps integrate first,
then resolve floor, left-wall, and right-wall contacts. Inward normal velocity
changes according to `vn_after = -e*vn_before`; tangential velocity is unchanged.
Contact detection includes exact touching. There is no continuous impact-time
resolution, drag, friction, ceiling collision, or resting-contact threshold.

## Independent reference cases

The derivations were explained before writing tests and are retained in the
test docstrings. Expected answers use analytical formulas, literal hand-calculated
values, and loop time, not simulator reference, energy, or time helpers.

### Upward launch through the apex

Initial position is `(8, 3)` m, velocity `(-1.25, 4.905)` m/s, and gravity
`g=9.81 m/s^2`. The interval is one second. A 20 by 20 m box keeps the
trajectory clear of every contact boundary. Constant gravity and no drag give:

```text
x(t)  = 8 - 1.25*t
vx(t) = -1.25
vy(t) = 4.905 - 9.81*t
y(t)  = 3 + 4.905*t - 9.81*t^2/2
```

The apex occurs at `t=0.5 s`, with `x=7.375 m`, `y=4.22625 m`, and `vy=0`.
At one second the exact continuous state is `(6.75, 3, -1.25, -4.905)`.
Summing the velocity-first updates independently gives:

```text
vy_k = vy_0 - k*g*h
y_n = y_0 + n*h*vy_0 - g*h^2*n*(n+1)/2
y_n - y(n*h) = -g*h*t/2
```

Thus numerical endpoint heights must be `2.95095 m` for `h=0.01 s` and
`2.975475 m` for `h=0.005 s`. Velocity and horizontal position have no
truncation error for this constant-acceleration case.

The test checks every timestep, including ascent, apex, and descent, for both
`step` and `complete_step`, both timesteps, and masses 0.25 and 7 kg: eight
parameter combinations. Motion is mass-independent because gravitational
force divided by mass is `-g`. Complete-step runs must produce no contacts.

### Aligned elastic wall reflection

Set `g=0`, restitution `e=1`, radius `r=0.25 m`, and box width `W=4 m`.
Initial position is `(1, 2)` m and velocity `(2, 0.5)` m/s. The center reaches
the right boundary at `W-r=3.75 m`, so impact time is `(3.75-1)/2=1.375 s`.

```text
Before impact:       x(t) = 1 + 2*t,                vx = 2
At/after impact:     x(t) = 3.75 - 2*(t-1.375),     vx = -2
Throughout:          y(t) = 2 + 0.5*t,              vy = 0.5
```

The state at impact uses the post-impact velocity convention. At two seconds,
the expected state is `(2.5, 3, -2, 0.5)`. Steps of `1/16` and `1/32 s`
align impact exactly at steps 22 and 44. These binary-exact inputs and increments
avoid both integration truncation error and within-step impact-time error.
Every step is checked, including the single right-wall contact, its zero
position correction, and normal velocities `-2` before and `+2 m/s` after.

This adds two parameter combinations, for ten across the two test methods.

## Tolerance rationale

The tests use `math.isclose` with absolute tolerance `1e-11` in the compared
quantity's SI unit and relative tolerance `1e-13`. Its acceptance bound is
`max(atol, rtol*max(abs(actual), abs(expected)))`. With at most 200 steps and
position/speed scales below 9, the conservative roundoff estimate
`8*N*epsilon*scale` is below `3.2e-12` for binary64 arithmetic. The absolute
allowance covers accumulated roundoff, including cancellation near zero apex
velocity. The relative allowance is smaller than the absolute allowance for
these cases and does not enlarge their effective bound.

Euler's O(h) height error is explicitly checked as the signed bias `-g*h*t/2`;
it is not absorbed into the roundoff tolerance. The aligned wall case has no
truncation error. Counts, contact presence, and exactly zero wall correction
use exact assertions. Tolerances were chosen before execution and never loosened.

## Original first-step verification

Working directory: `D:\CodexCLI\vibecoding\HW3_submission`.
Interpreter: CPython 3.12.10, 64-bit Windows. The initial sandbox could not
access the interpreter; `uv python list --only-installed` located it, and the
test commands ran after sandbox approval.

Commands actually executed before relocation (the first command is historical
and is superseded by the module command below):

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B check_analytical.py
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v check_integration check_contacts check_scheduling check_cli
git diff --check
```

- New suite: two tests passed, exercising all ten parameter combinations.
- Largest launch height-bias residual: `2.30e-15 m` (coarse); fine runs reported
  `2.13e-15 m`.
- Both reflection runs reached exactly `(2.5, 3.0, -2.0, 0.5)`.
- All 26 existing regression tests passed. The CLI suite used temporary
  headless figure output and did not launch a GUI.
- All three verification commands exited successfully.
- No test failed; no implementation bug, test error, or SPEC ambiguity required
  a fix. These cases do not establish accuracy for unaligned impacts or rotation.

The first-step changes were the new analytical suite and a root README update.
Simulator source and SPEC were unchanged.

## Relocation

Deliverables now reside in `hw4/`: `check_analytical.py`, `README.md`, and this
report. The root README points here and uses the updated command. The test's
invocation docstring was updated; assertions and tolerances are unchanged.
Module execution from the root keeps simulator imports available without
moving source files or modifying `sys.path`.

Current execution command from `D:\CodexCLI\vibecoding\HW3_submission`:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.check_analytical
```

Relocation verification: the command above ran successfully from that root
directory on Python 3.12.10, exit code 0. Both tests passed across all ten
parameter combinations (reported runtime 0.013 s). The maximum launch
height-bias residual remained `2.30e-15 m`; both wall endpoints remained exact.
This run verified imports from the unchanged root simulator modules. The
26-test regression result above belongs to the original first-step run; those
suites were not rerun solely for this relocation.
