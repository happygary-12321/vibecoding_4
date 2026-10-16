# Part 3: convergence-order testing results

This is an explicitly agent-generated factual report, not the user's personal
testing log. Earlier reports are preserved unchanged as historical records.

## Inspection and assumptions

Reviewed SPEC's motion equations and integration method, `integration.py`,
the existing integration/refinement tests, the HW4 analytical and conservation
tests, both earlier reports, and the READMEs before implementation.

The simulator represents a translating 2D circle in SI units, with +x rightward
and +y upward. The test assumes constant nonzero gravity, no drag or rotation,
and no contacts. A fresh state is used for every refinement level. Both
`step` and `complete_step` are exercised with standard-library `unittest`
subtests. Complete steps must return an empty contact list at every step.

Initial position is `(10,20)` m; initial velocity is `(1.3,2.7)` m/s;
gravity is 9.81 m/s^2; radius is 0.2 m; the box is 100 by 100 m. The final
time is T=1.5 s. The horizontal path stays between x=10 and 11.95 m. The
continuous vertical maximum is `20+2.7^2/(2*9.81) < 20.372 m`, and its
minimum over the interval is 13.01375 m. Even the coarse discrete endpoint
is 12.55390625 m. Thus the paths are comfortably clear of all boundaries.
Every numerical sample additionally asserts a clearance exceeding one meter
from the floor and side walls, and stays below the displayed box height.

## Independent analytical derivation

Integrating `dvx/dt=0`, `dvy/dt=-g`, and position derivatives gives:

```text
vx(t) = vx0
vy(t) = vy0 - g*t
x(t) = x0 + vx0*t
y(t) = y0 + vy0*t - 0.5*g*t^2
```

At T=1.5 s, the exact state is
`(x,y,vx,vy)=(11.95,13.01375,1.3,-12.015)` in SI units.
Expected values use these expressions directly. No production reference or
time helpers are called; elapsed endpoint time is checked using integer count
times the independently chosen h.

For velocity-first semi-implicit Euler, summing the updated velocities gives:

```text
vy_k = vy0 - k*g*h
y_N = y0 + N*h*vy0 - 0.5*g*h^2*N*(N+1)
y_N - y(T) = -0.5*g*T*h, where T=N*h
```

The measured error is `E(h)=abs(y_N-y(T))`, without bias subtraction or any
correction to numerical position. The bias formula is only an additional
signed-error assertion. For this case, `E(h)=C*h` with nonzero `C=g*T/2`,
so halving h should halve E and yield `q=log2(E(h)/E(h/2))=1`.
Three successive refinement ratios demonstrate this behavior over four levels,
rather than relying on one comparison. Horizontal position and both velocity
components have only roundoff error here and are checked separately; they are
never used to estimate convergence order.

## Timestep choices and tolerances

| h (s) | Integer steps N | Endpoint N*h (s) | Expected error magnitude (m) |
| --- | --- | --- | --- |
| 1/16 = 0.0625 | 24 | 1.5 | 0.45984375 |
| 1/32 = 0.03125 | 48 | 1.5 | 0.229921875 |
| 1/64 = 0.015625 | 96 | 1.5 | 0.1149609375 |
| 1/128 = 0.0078125 | 192 | 1.5 | 0.05748046875 |

These h and T values are exactly representable in binary64. Step counts are
specified integers, not obtained by rounding T/h. Both planned and actual
counts times h are asserted equal to T; every increment is checked. There is
no interpolation and no comparison of different physical endpoint times.

Position and velocity comparisons use `math.isclose` with absolute tolerance
1e-11 m or m/s, respectively, and relative tolerance 1e-13. The effective bound
is `max(atol, rtol*max(abs(actual),abs(expected)))`. With at most 192 steps and
state magnitudes below 25, the conservative estimate `8*N*epsilon*25` is below
8.6e-12 for binary64. The absolute tolerance dominates at these scales and
covers accumulated arithmetic and reference evaluation roundoff. The vertical
position tolerance applies to the signed bias formula, not to a claim that the
uncorrected numerical height is within 1e-11 m of the continuous height.

The smallest truncation error, about 0.0575 m, exceeds the 1e-11 m roundoff
budget by over five billion times. The test explicitly requires nonzero error
greater than one million times that budget and strict decrease at each level.

The separate observed-order assertion is `abs(q-1) <= 1e-9`, with no relative
allowance. To first order in endpoint roundoff delta, propagation through the
ratio and logarithm gives:

```text
abs(delta_q) <= (delta/E_coarse + delta/E_fine)/ln(2)
```

Taking delta=1e-11 m for both errors in the finest pair yields less than
3.8e-10. The selected 1e-9 tolerance adds margin for ratio/log evaluation;
higher-order terms in delta/E are negligible. This is a narrow roundoff-based
order interval, not a broad empirical range. No tolerance was changed after
execution.

## Measured results

Both entry points produced the following values, printed at 15 significant
digits. Ratio and q on each refined row compare the preceding level to that
row. All signed errors were negative. The coarsest row has no preceding pair.

| h (s) | N | Measured absolute endpoint error (m) | Error ratio | Observed q |
| --- | --- | --- | --- | --- |
| 0.0625 | 24 | 0.459843749999999 | — | — |
| 0.03125 | 48 | 0.229921875000002 | 1.99999999999998 | 0.999999999999983 |
| 0.015625 | 96 | 0.114960937499994 | 2.00000000000012 | 1.00000000000009 |
| 0.0078125 | 192 | 0.0574804687499881 | 2.00000000000031 | 1.00000000000022 |

All eight trajectories (two APIs times four levels) reached exactly T=1.5 s.
All six order comparisons passed. Maximum observed deviation of q from 1 was
approximately 2.2e-13. Horizontal position and both velocity checks passed;
step counts and all clearance checks passed. Every `complete_step` call
returned no contacts. Output was the same in the standalone and combined runs.

## Actual commands and verification

Working directory: `D:\CodexCLI\vibecoding\HW3_submission`.
Interpreter: CPython 3.12.10, MSC v.1943, 64-bit Windows AMD64. HW4 has no
exact patch-version execution guard; no other interpreter was tested.
Commands used the installed interpreter with sandbox approval:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.check_convergence
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v hw4.check_analytical hw4.check_conservation hw4.check_convergence
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v check_integration check_contacts check_scheduling check_cli
```

| Run | Actual result | Reported unittest runtime | Exit code |
| --- | --- | --- | --- |
| Part 3 alone | 1 test method passed, 8 trajectory subcases | 0.001 s | 0 |
| Parts 1–3 together | 7 test methods passed | 0.069 s | 0 |
| Existing regression suite | 26 test methods passed | 6.328 s | 0 |

The existing CLI regression included its temporary headless figure test.
No GUI was launched or saved figure evidence overwritten.

## Failures, changes, and limitations

There were no initial test failures, so no test, implementation, or tolerance
fixes were needed. The physical requirements and simulator source were not
changed. New files are `hw4/check_convergence.py` and this report;
`hw4/README.md` and the root README were updated with scope, links, and commands.
Earlier tests, reports, and SPEC remain unchanged. No intentional bugs or
commits were introduced.

Passing this smooth-flight test demonstrates first-order vertical-position
convergence for the tested constant-gravity, collision-free problem. It does
not establish convergence order across collisions, where endpoint detection
and projection introduce additional timing and position errors.
