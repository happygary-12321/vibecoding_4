# HW4 function-coverage audit results

This is an explicitly agent-generated factual report, not the user's personal
testing log. No transcript references are fabricated. Parts 1–5 reports remain
unchanged as historical records.

## Outcome and scope

The [function inventory](function_coverage.md) maps each handwritten simulator
function/method, including nested callbacks, to exact test names, concrete
assertions, direct/indirect coverage, and remaining gaps. The simulator scope
is the eight production modules in SPEC section 6. Test infrastructure,
generated artifacts, and historical submission/report-maintenance tools are
excluded with explicit reasons.

Every **major simulator function now has a meaningful associated test** in
that scope. This is an assertion-based audit, not a line-execution percentage
or a claim of exhaustive branch coverage. GUI functions have headless fake-
backend application-logic tests; native GUI behavior remains a gap. Plotting
has a real Agg artifact-generation test; pixel/curve/label correctness remains
a gap. Adequate legacy tests are reused rather than copied into HW4.

## Added verification

`hw4/check_function_coverage.py` contains 18 unittest methods: the 16 draft
audit cases below plus the two completion-review cases documented at the end.

1. Unsupported field types and revalidation after state mutation; independent
   nonzero-count time value .875 s, preserving state.
2. Exact-diameter geometry rejected by integration/contact/scheduler paths;
   complete-step and resolver leave state unchanged; scheduler rejects invalid
   mutable state.
3. Scheduler snapping within 8 ulps versus flooring outside, actual state
   displacement/counts, remainder and elapsed-time accumulation, quotient
   overflow rejection before mutation. Legacy cap/discard tests remain reused.
4. Whole-step bounds (1 and 1,000,000 inclusive), near-integer acceptance,
   nonalignment, nonpositive/nonfinite inputs and quotient overflow.
5. Experiment count tuple (4,8,16), continuous and discrete floor guards,
   fine-run step cap, invalid bounce alignment.
6. Independent tolerance budgets and report-check boundary/NaN/inf/boolean
   pass/fail behavior.
7. Snapshot values, energy/time, no state mutation, and no later aliasing.
8. Free-fall history against independent discrete/continuous position,
   velocity, energy and energy-drift formulas for nondefault parameters.
9. Bouncing report with an independently hand-calculated first impact and
   energy accounting, for e=.5 and e=1.
10. Contact-direction report values, preserved upward velocity and no impact.
11. Embedded regression count, failure lists and captured test output.
12. Invalid validation setup before directory creation and failed-report
   persistence after a controlled plotting I/O error.
13. Figure-entry custom parsing/dispatch and failed-report/OSError/unexpected-
   exception policies. Legacy real headless success test remains reused.
14. GUI dependency classification: missing PyVista/VTK translated, unrelated
   missing-module errors propagated.
15. GUI callback/application lifecycle using fake backend and clock, but real
   integration and scheduler; actor endpoint/status/count plus timer/callback
   error handling and cleanup.
16. Complete-runner contract in temporary trees: both directories' check files
   execute, synthetic test failure and import error produce exit 1.

Temporary synthetic failure/import probes and mocked dependency/I/O failures
are unit-test stimuli. No production code was intentionally broken; these are
not the assignment's pending intentional-bug experiment.

The small-e test in `hw4/check_limiting.py` now captures the pre-impact state
velocity and checks `normal_velocity_before` against both -3.2 and that state.
It checks `normal_velocity_after` against independently expected `3.2*e` and
actual post-impact state. Outgoing record checks retain **zero absolute
tolerance**, relative tolerance 1e-12, including an exact zero expectation at
e=0. All original small-e positivity, energy, and monotonicity checks remain.

## Independent reference details and tolerances

For `free_fall`, g=2, m=3, h=1/8 and N=4 give at step n:
`t=n/8`, `y=10-n(n+1)/64`, `vy=-2t`, continuous `y=10-t^2`, and
energy `6*y+1.5*(2t)^2`. Signed height error is `-t/8`; energy drift is
`-3t/4`. At T=.5: y=9.6875, vy=-1, E=59.625 J, drift=-.375 J.

For `bouncing`, default initial position/velocity, g=2, m=3, r=.25 and h=.25
give first floor contact at step 5: pre-y=.125, pre-vy=-2.5. Projection adds
.125 m, or .75 J of potential energy. At e=.5, kinetic loss is -7.03125 J;
at e=1 it is zero. After six steps the independent endpoints are
`(x,y,vx,vy)=(3.25,.4375,1.5,.75)` with E=6.84375 J and
`(3.25,.75,1.5,2)` with E=13.875 J, respectively. Cumulative integration drift
is -2.25 J. These are accounting checks, not exact mechanical-energy conservation.

The fake GUI callback test uses timer values 0,.25,.5 s with h=.125 and g=2.
The first event starts the clock, so four real steps advance the default state
to actor position `(1.75,1.6875,0)` and simulated time .5 s. This is stronger
than checking only that a scheduler/callback mock was invoked.

New scalar numerical checks use absolute 1e-12 in the corresponding SI unit:
at most six physics steps and values below 100 mean even a conservative
32*epsilon*100 arithmetic scale is below 7.2e-13. The dyadic fixtures make many
values exactly representable. Scheduler time comparisons also use 1e-12 s,
while exact step counts distinguish rounding branches. Tolerance-policy checks
use exact powers of two (2^-49 and 2^-29); threshold acceptance tests use
representable .125 and nextafter to avoid broad tolerances. Discrete counts,
identities, flags, strings, and immutable-state checks use exact assertions.
No earlier physics tolerances were changed.

## Complete runner

`hw4/run_tests.py` enumerates all current `check_*.py` files directly in the
repository root and in `hw4/`, importing each by its module name. These are
the locations of all current regression suites. It prints each module and test
count; unlike default discovery it cannot miss them because their names do
not start with `test`. Empty modules/no test files are rejected. Imports are
not caught or skipped. Test failure/error yields exit 1, and an uncaught import
error also yields nonzero exit. Files in future additional test directories
would require an explicit extension of the runner's documented scope.

The completed runner includes 10 modules:

| Module | Top-level test methods |
| --- | ---: |
| check_cli | 9 |
| check_contacts | 6 |
| check_integration | 5 |
| check_scheduling | 6 |
| hw4.check_analytical | 2 |
| hw4.check_conservation | 4 |
| hw4.check_convergence | 1 |
| hw4.check_function_coverage | 18 |
| hw4.check_limiting | 4 |
| hw4.check_symmetry | 3 |
| **Total** | **58** |

Embedded legacy tests invoked by validation helpers and subprocess probes are
additional internal executions, not extra top-level method counts.

The complete suite needs the declared plotting dependencies for the legacy
CLI smoke test. A missing dependency causes failure, not a skip. Its real
headless validator runs in a subprocess because `run_validation` explicitly
rejects preloaded rendering/PyVista modules, while scheduler tests legitimately
import rendering in the parent test process. All file-writing tests use fresh
TemporaryDirectory paths. Fake backend patches are scoped and restored. No
native GUI was launched and saved outputs were not overwritten.

## Prior draft's recorded failure, investigation, and fix

The following failure and 55/56-test timings were already recorded in this
working-tree report when the completion review began. They are retained as
prior-stage history, not claimed as executions observed during this review.
The completion review's actual executions are recorded separately below.

The first complete invocation ran 55 test methods and exited **1**, reporting
two subcase errors (e=.5 and e=1) in
`test_bouncing_report_independent_first_impact_accounting`:
`KeyError: 'measured_contact_kinetic_change'`.

Inspection of `validation.bouncing` showed that per-contact records expose
`measured_kinetic_change`; `measured_contact_kinetic_change` belongs to the
per-step sample schema. The new test used the wrong dictionary key. This was
a **test error**, not an implementation bug or SPEC ambiguity. The lookup was
corrected to `measured_kinetic_change`, keeping all expected numeric values and
tolerances unchanged. A runner-contract test was also added, accounting for
the final increase from 55 to 56 methods. No production change was necessary.

## Prior draft's commands and results

Working directory: `D:\CodexCLI\vibecoding\HW3_submission`.
Interpreter: CPython 3.12.10, MSC v.1943, 64-bit Windows AMD64.
The same command was run twice with sandbox approval for the installed interpreter:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
```

| Invocation | Result | Reported unittest runtime | Exit |
| --- | --- | --- | --- |
| Initial | 55 methods, 2 subcase errors from incorrect test field name | 6.002 s | 1 |
| After correction and runner-contract addition | **56 methods passed** | **6.037 s** | **0** |

The temporary runner-contract subprocesses returned 0 for two passing probes,
1 for a synthetic assertion failure, and 1 for a synthetic import error, as
asserted by the passing parent test. The intentional exception stimuli in
failure-path tests are expected outcomes, not failed tests.

## Changed files

- New `hw4/check_function_coverage.py`: 18 meaningful gap/infrastructure tests.
- New `hw4/run_tests.py`: complete-suite entry point.
- New `hw4/function_coverage.md`: function inventory and assertion mapping.
- New `hw4/coverage_results.md`: this agent-generated factual report.
- Updated `hw4/check_limiting.py`: independent pre/post contact-record checks.
- Updated `hw4/README.md` and root README: complete command, dependencies, audit
  links, and current scope/status.

Simulator source, SPEC, legacy suites, other HW4 tests, and all five earlier
step reports remain unchanged. No git commit or intentional production bug was
introduced. No personal log or transcript reference was authored.

## Remaining limitations and assignment work

The meaningful-test association requirement is met for the major simulator
functions, with GUI functions explicitly limited to fake-backend application
logic. Native window/input/timer/close behavior and backend compatibility still
need a separately authorized manual/integration GUI check if the assignment
requires that scope. Plot visual fidelity and plotted-series correspondence
are not established by PNG signature tests. Maintenance tools and exhaustive
I/O/defensive branches are outside this completed audit's claim.

No statement of 100% line/branch coverage is made. The meaningful new checks
do not extend the physical model, prove convergence across collisions, or
remove numerical resting/contact-time limitations. The intentional-bug
experiment remains pending authorization; the user still needs a personally
written log with real transcript references, and reviewed git commits remain
pending. These reports do not substitute for those requirements.

## Completion review and actual verification (2026-10-16)

This section is agent-generated from the current review's tool results.
At entry, root README was modified and all of `hw4/` was untracked, including
the draft audit, runner, gap tests, and strengthened small-e record assertions.
The existing work was reviewed and retained. The five step reports were not
edited. All eight simulator modules, SPEC, the four legacy suites, and HW4
Parts 1-5 were inspected for the function-to-assertion mapping.

Two additional meaningful gaps were addressed in `check_function_coverage.py`:

- `test_repeated_overload_accumulates_discarded_time`: h=1/8, initial count 7,
  g=0, position (10,10), velocity (.5,.25). Intervals 8.8125, 9.96875,
  .09375, and 0 seconds must execute 60,60,1,0 steps. Discards accumulate
  from 10 to 30 steps (1.25 to 3.75 seconds); remainders are .0625,
  .03125,0,0. Every update checks independent positions
  `(10+N/16,10+N/32)`, actual count `7+N`, unchanged velocities and exact
  elapsed = newly simulated + discarded + remainder. All inputs/results
  are binary-exact; assertions require equality, with no tolerance increase.
- `test_side_walls_above_displayed_height`: both walls at y=8, above H=3,
  with r=.25, W=6, e=.5. Inward speed 3 becomes outward 1.5; signed
  corrections are +.125 and -.125. Positions, normal records, impact flag,
  preserved tangent, and unchanged count are asserted exactly. This closes
  a SPEC-specific gap left by interior no-ceiling and below-height cases.

The small-e test already checks record velocities independently against -3.2
and 3.2*e and against actual pre/post state. Those assertions were reviewed,
retained, and rerun; no duplicate test or weakened assertion was introduced.
The inventory and both READMEs were updated for the two additions and 58-test
complete suite. Production source, SPEC, runner, and legacy tests needed no fix.

An initial sandboxed source-inspection command could not access the installed
Python executable (PowerShell CommandNotFoundException). `uv python list
--only-installed` located CPython 3.12.10; the full-suite command ran with
sandbox escalation. This was an environment-access issue, not a test failure.

Command executed twice from `D:\CodexCLI\vibecoding\HW3_submission`:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
```

| Current-review invocation | Result | unittest runtime | Exit |
| --- | --- | --- | --- |
| Before the two additional cases | 56 tests passed | 4.699 s | 0 |
| After the two additional cases | 58 tests passed | 4.361 s | 0 |

No current-review test failed. No implementation or tolerance fix was needed.
The runner's temporary failure/import-error probes passed their expected
nonzero-exit assertions. Actual file outputs remained temporary and headless.
`git diff --check` passed with exit 0. Because HW4 is untracked, its files are
also checked individually using
`git -c core.autocrlf=false diff --no-index --check -- NUL <file>`.
All 15 files produced no whitespace diagnostics. The first wrapper incorrectly
treated no-index's exit 1 (file differs from NUL) as a whitespace failure;
inspection found only line-ending conversion warnings, no whitespace errors.
The corrected wrapper accepts 0/1 only when diagnostics are empty and rejects
higher statuses. It passed with exit 0; no file content was changed for this.
No commit, intentional production defect, personal log, or transcript reference
was created. Every major function has a meaningful associated test within the
documented scope; native GUI behavior, plot visual fidelity, exhaustive branches
and extreme inputs remain the explicit limitations above.
