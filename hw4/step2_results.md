# Part 2: conservation-property testing results

This is an explicitly agent-generated factual report, not the user's personal
testing log. All new deliverables reside in `hw4/`. No intentional bugs or
commits were introduced.

## Inspection and physical assumptions

Reviewed the HW4 analytical suite, README, and Part 1 report; root README;
`assign3/SPEC.md`; state, integration, contacts, and validation implementation;
and the existing integration, contact, scheduling, and CLI tests.

The model is a translating 2D circle with state `(x,y,vx,vy,step_count)` in SI
units, +x rightward and +y upward. It has no rotation, friction, drag, or ceiling.
Semi-implicit Euler updates velocity before position, then complete steps
resolve floor/left/right endpoint contacts. Normals into the allowed region
are floor `(0,1)`, left `(1,0)`, right `(-1,0)`. Restitution acts only on
inward normal motion; the tangent is unchanged. Walls are fixed external bodies.

All Part 2 trajectories set gravity to zero. This removes gravitational work,
Euler's gravity-dependent energy drift, and potential-energy effects from
position projection. Impact timing is discrete; these tests check invariants
and responses, not continuous collision times. They never require exact
mechanical-energy conservation under gravity. Particle momentum is tested only
in contact-free flight: a fixed wall supplies an external impulse.

## Independent references and test rationale

Test-local functions compute momentum `p=(m*vx,m*vy)` in kg*m/s and kinetic
energy `K=m*(vx*vx+vy*vy)/2` in J directly from state. No production helper
generates these references. Pre-step velocities equal pre-impact velocities
when g=0. Each collision fixture asserts at most one contact per step, so
pre/post state directly tests the normal and tangent without ambiguity from
corner collisions. Contact-record velocities are checked against state values,
not used as the physics oracle.

### 1. Gravity-free free flight

Three runs use masses 0.25, 2.5, and 1000 kg, initial position `(50,50)` m,
velocity `(1.7,-0.9)` m/s, box `(100,100)` m, and 1024 steps of `1/128 s`.
The exact eight-second endpoint `(63.6,42.8)` is safely inside the box.
With no force, `dv/dt=0`, so both nonzero momentum components and K must remain
constant. Every step asserts an empty contact list, step count, momentum, and K.

| Mass (kg) | Initial momentum (kg*m/s) | Initial K (J) |
| --- | --- | --- |
| 0.25 | (0.425, -0.225) | 0.4625 |
| 2.5 | (4.25, -2.25) | 4.625 |
| 1000 | (1700, -900) | 1850 |

### 2. Repeated elastic collisions

Two independent 16-second trajectories use `m=2.5 kg`, `e=1`, radius 0.2 m,
box `(4,30)` m, initial position `(2,1.5)` m, and velocities `(-2.3,-1.1)`
and `(2.3,-1.1)` m/s. Each advances 1024 steps of `1/64 s`.
Initial K is `2.5*(2.3^2+1.1^2)/2=8.125 J`.

For a frictionless elastic wall, `vn_after=-vn_before` and
`vt_after=vt_before`, so the squared speed, and hence K, are unchanged.
Each step checks K against its initial value. Each impact additionally checks
K before/after, unchanged tangent, inward-to-outward normal reversal, and record
consistency. Each trajectory must hit the floor exactly once and each side wall
at least four times. Simultaneous contacts are asserted absent.

Without gravity or a ceiling, upward motion after a floor impact cannot return
to the floor. Repeated floor bounces in a single trajectory would contradict
this model. Two independent launches provide two floor impacts overall, plus
repeated left/right impacts, without resetting a live trajectory or adding forces.

### 3. Inelastic collision energy balance

Six single-step cases cover all three surfaces at `e=0.3` and `e=0.8`, with
`m=2.5 kg`, `h=0.1 s`, normal speed 2.3 m/s and nonzero tangent speed 1.1 m/s.
The floor fixture starts at `(2,0.3)` with velocity `(1.1,-2.3)`; left starts
at `(0.3,2)` with `(-2.3,1.1)`; right starts at `(3.7,2)` with `(2.3,1.1)`.
Each crosses exactly its intended boundary in the default box.

Decomposing energy as `K=m*(vn^2+vt^2)/2`, tangent preservation cancels the
tangential term. Substituting `vn_after=-e*vn_before` yields independently:

```text
K_after - K_before = -0.5*m*(1-e^2)*vn_before^2
```

Expected losses are `-6.017375 J` at e=0.3 and `-2.3805 J` at e=0.8.
The test checks this balance using energies calculated from actual state,
normal response and tangent preservation, the intended contact, and strict
energy decrease. These are energy-balance tests, not energy conservation.

### 4. Production energy helper

There is no production momentum helper. `validation.energy` computes total
mechanical energy, so it is tested separately on static states against
`K+m*g*y` and hand-calculated values. With m=2.5 kg and velocity `(-3,4)`,
K=31.25 J. At g=9.81 and y=2, potential energy is 49.05 J and total is 80.3 J.
Additional rest states check 49.05 J at y=2 and 0 J at y=0. No integration or
conservation assertion under gravity is involved. Importing validation requires
only the standard library; plotting imports are deferred inside production code.

## Tolerance rationale

Part 2 uses `math.isclose` with `abs_tol=1e-12` in the compared quantity's unit
(J, kg*m/s, or m/s), and `rel_tol=1e-13`. Acceptance is
`abs(actual-expected) <= max(atol, rtol*max(abs(actual),abs(expected)))`.
Both operands must be finite.

Binary64 epsilon is about 2.22e-16. A conservative allowance of 32 epsilon for
the few products and sums in an independent p, K, or loss evaluation is about
7.1e-15 relative. The selected relative allowance adds margin; for the largest
K of 1850 J its contribution is 1.85e-10 J, and for momentum 1700 kg*m/s it is
1.7e-10 kg*m/s. At the 8.125 J collision scale and near zero, the absolute
1e-12 allowance dominates. Single-impact subtraction cancellation is covered
by that absolute allowance. Inelastic losses are several joules, so strict
energy decrease needs no numerical slack.

There are up to 1024 steps per trajectory, but neither reference nor measured
momentum/energy is summed across those steps. At zero gravity and e=1, velocity
components are preserved or sign-reversed, with no accumulation of velocity
roundoff; position accumulation does not enter K. Accordingly the tolerance
does not grow with step count. There is no truncation-error budget hidden in
these comparisons. Part 1 retains its original tolerances and explicit Euler
height-bias check. All tolerances were set before testing and were not loosened.

## Interpreter policy

SPEC section 6 describes exact Python 3.12.10 guards in the four legacy scripts,
but does not prescribe that patch version for HW4 or all runtime entry points.
The analytical suite's exact-version guard was removed as requested. Part 2
also has no patch-version guard. Legacy scripts and SPEC are unchanged.
The tested interpreter is CPython 3.12.10, MSC v.1943, 64-bit Windows AMD64;
no other version was tested. The Part 1 report preserves historical results.

## Commands and results

Working directory: `D:\CodexCLI\vibecoding\HW3_submission`.
The following commands were actually run, with sandbox approval to access the
installed interpreter:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.check_conservation
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v hw4.check_analytical hw4.check_conservation
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v check_integration check_contacts check_scheduling check_cli
```

| Run | Result | Reported unittest runtime | Exit code |
| --- | --- | --- | --- |
| Part 2 alone | 4 tests passed | 0.065 s | 0 |
| Parts 1–2 together | 6 tests passed | 0.068 s | 0 |
| Existing regression suite | 26 tests passed | 6.132 s | 0 |

Part 2 covers 15 parameter combinations: 3 free-flight runs, 2 elastic
trajectories, 6 inelastic cases, and 4 static helper cases. Part 1 retains its
10 combinations. These are subcases, not additional unittest method counts.

- All free-flight momentum and energy drifts measured zero.
- Each elastic run recorded floor=1, left=5, right=5 impacts; K drift measured
  zero. Across both trajectories, all 22 impacts passed normal/tangent checks.
- All six inelastic cases lost energy. Balance residuals were +8.88e-16 J
  at e=0.3 and -8.88e-16 J at e=0.8 (maximum absolute 8.88e-16 J).
- All four energy-helper values passed.
- Part 1 maximum launch height-bias residual remained 2.30e-15 m; wall
  reflection endpoints remained exact.
- Existing CLI regression testing included its temporary headless figure run;
  no GUI was launched and no saved figure evidence was overwritten.

## Initial failures, fixes, and changed files

There were no initial test failures, and no implementation or tolerance fixes.
The version guard removal is an execution-policy change, not a physics fix.
The new tests do not establish exact impact timing or conservation under gravity.

Changed in Part 2:

- `hw4/check_conservation.py` (new): independent references and four tests.
- `hw4/step2_results.md` (new): this agent-generated report.
- `hw4/check_analytical.py`: remove exact patch-version guard and update invocation text.
- `hw4/README.md`: Part 2 scope, individual/combined commands, interpreter policy.
- Root `README.md`: consistent HW4 scope, report links, and combined command.

Simulator source, SPEC, legacy tests, and the historical Part 1 report are
unchanged. No commits or intentional bugs were introduced.
