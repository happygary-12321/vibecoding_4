# HW4 intentional-bug experiment

**Agent-generated factual report.** This is not the user's personal testing
log. No transcript references are asserted. The user explicitly authorized
one temporary production defect; tests, expected values, tolerances, and SPEC
must remain unchanged. No commit or push is authorized.

## Passing baseline and preservation

On 2026-10-16, the complete suite passed: **58 tests, 4.405 s, exit 0**,
using CPython 3.12.10. Starting status was ` M README.md` and `?? hw4/`.
Existing changes are preserved. The exact original bytes of `contacts.py`
are saved as [contacts.py.before](bug_experiment/contacts.py.before).
Protected-file hashes cover all root Python sources, all HW4 check suites,
the runner, SPEC, all five step reports, and both coverage reports.

The actual full-suite command, also saved with the working directory, is:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
```

Baseline evidence: `bug_experiment/baseline.command.txt`,
`baseline.stdout.txt`, `baseline.stderr.txt`, `baseline.exit.txt`,
`baseline.git_status.txt`, and `protected.before.json`.

## Predictions recorded before mutation

This section was written after the passing baseline and before introducing or
running the defect. The driver will preserve this report's current bytes in
`bug_experiment/predictions.before_mutation.md` before editing production code.

Inspected implementation: `contacts.resolve_contacts` handles floor, left,
then right. Only the right-wall inward branch `if state.vx > 0` will change:

```diff
-            state.vx = -restitution * state.vx
+            state.vx = -state.vx
```

The right wall will incorrectly act elastically for e<1, retaining normal
kinetic energy instead of removing `m*(1-e^2)*vn_before^2/2`. At e=0 the
circle will rebound rather than stop normally. Projection, direction guards,
floor/left response, tangential motion, and record construction are unchanged.
At e=1 there is no behavioral difference. This is an executable physics
defect, not a mock or syntax/import error.

Expected direct failures (exact existing method names):

| Test | Predicted failing cases and reason |
| --- | --- |
| `check_contacts.ContactChecks.test_surfaces_and_directions` | right, inward normal=-2, touching=False and True: vx=-2 instead of -1.6 |
| `check_contacts.ContactChecks.test_both_corners` | right corner: vx=-2 instead of -.8*2; left corner should pass |
| `check_contacts.ContactChecks.test_restitution_endpoints` | right wall at e=0: vx=-2 instead of 0; e=1 cases should pass |
| `hw4.check_conservation.ConservationChecks.test_inelastic_collision_energy_balance` | surface=right at e=.3 and .8: outgoing speed 2.3 instead of .69 or 1.84; normal-response assertion may fail before energy assertion |
| `hw4.check_function_coverage.FunctionCoverageChecks.test_side_walls_above_displayed_height` | surface=right: vx=-3 instead of -1.5 |
| `hw4.check_limiting.LimitingChecks.test_zero_restitution_impact_and_followup` | surface=right: vx=-3.2 instead of zero on first impact |
| `hw4.check_symmetry.SymmetryChecks.test_colliding_horizontal_reflection` | restitution=.8: left and right responses no longer map under reflection; failures can cascade across step subtests. e=1 should pass |

Expected secondary failures:

| Test | Reason |
| --- | --- |
| `check_cli.CliChecks.test_headless_figures` | The short numerical trajectory itself need not reach a wall; embedded contact regressions should fail, causing failed report/CLI exit 1 instead of 0 |
| `hw4.check_function_coverage.FunctionCoverageChecks.test_embedded_regression_report` | Embedded legacy regressions should return passed=False and nonempty failures |
| `hw4.check_function_coverage.FunctionCoverageChecks.test_validation_failure_serialization_and_invalid_setup` | Its controlled plotting-error path still occurs, but the assertion that embedded regressions passed should fail |

Expected passes of interest:

- `hw4.check_analytical.AnalyticalChecks.test_aligned_elastic_wall_reflection`
  and `hw4.check_conservation.ConservationChecks.test_repeated_elastic_collisions`:
  e=1 masks this defect.
- `hw4.check_symmetry.SymmetryChecks.test_mass_invariance`: the wrong law is
  still mass-independent, so paired states may agree despite wrong physics.
- `check_contacts.ContactChecks.test_default_trajectory`: finite bounds and
  occurrence of all surfaces may still hold; it does not assert inelastic speed.
- `hw4.check_limiting.LimitingChecks.test_approach_to_zero_restitution`: only
  the floor is tested; its strengthened records should remain correct.
- Analytical free flight, convergence, no-contact limits, validation contracts,
  scheduler tests, and mocked dispatch tests should generally pass because
  their asserted behavior does not distinguish this right-wall law.
- `hw4.check_function_coverage.FunctionCoverageChecks.test_bouncing_report_independent_first_impact_accounting`
  exercises the first floor impact but ends before a right-wall contact.

The prediction is **10 distinct failing test methods**, with more failure
entries possible because unittest records each failing subtest separately.
This is a prediction, not an observed result. No defect switch or test change
will be used if detection differs from this prediction.

## Execution and restoration plan

The saved `bug_experiment/experiment_driver.py` invokes the full runner in a
fresh process for each phase, recording separate complete stdout/stderr,
command and exit files. A byte-preserving `try/finally` restores `contacts.py`
from the pre-experiment backup even when the mutated subprocess errors,
times out, or the driver catches an interruption. The restored suite runs
in another fresh process. Final source bytes and protected hashes are checked.
No reset/clean operation or restoration from git HEAD is used.

Actual mutation/restoration results will be appended after execution.
