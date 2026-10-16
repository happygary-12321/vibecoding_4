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

## Actual results

Only the predicted one-line edit was applied. The saved
[intentional_bug.patch](bug_experiment/intentional_bug.patch) identifies the
right-wall assignment at line 189. No test, expected value, tolerance, or SPEC
was edited. Each full-suite invocation was a separate Python process.

| Phase | Methods run | Passing methods | Failing methods | Failure entries | Runtime | Exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 58 | 58 | 0 | 0 | 4.405 s | 0 |
| Mutated | 58 | 48 | 10 | 309 | 4.616 s | 1 |
| Restored | 58 | 58 | 0 | 0 | 4.725 s | 0 |

There were no unittest errors or skips. Failure entries include subtests and
must not be confused with distinct methods. Embedded regression executions
are internal work, not extra top-level methods in this table.

### Direct physical detections

| Exact failing method | Actual case(s); failure entries | Observed assertion |
| --- | --- | --- |
| `check_contacts.ContactChecks.test_both_corners` | Right corner, e=.8; 1 | vx=-2 versus -1.6 |
| `check_contacts.ContactChecks.test_restitution_endpoints` | Right wall, e=0; 1 | vx=-2 versus 0 |
| `check_contacts.ContactChecks.test_surfaces_and_directions` | `surface='right', touching=False, normal=-2` and `surface='right', touching=True, normal=-2`; 2 | vx=-2 versus -1.6 |
| `hw4.check_conservation.ConservationChecks.test_inelastic_collision_energy_balance` | `e=0.3, surface='right'` and `e=0.8, surface='right'`; 2 | Outgoing normal speed 2.3 versus .69 and 1.84; normal-response assertion fails before energy-balance assertion |
| `hw4.check_function_coverage.FunctionCoverageChecks.test_side_walls_above_displayed_height` | `surface='right'`; 1 | Actual state (5.75,8,-3,2,9) versus (5.75,8,-1.5,2,9) |
| `hw4.check_limiting.LimitingChecks.test_zero_restitution_impact_and_followup` | `surface='right'`; 1 | vx=-3.2 versus 0 on first impact |
| `hw4.check_symmetry.SymmetryChecks.test_colliding_horizontal_reflection` | `restitution=0.8`, every integer `step=103..400` inclusive; 298 | First mismatch: mirrored vx=2.504 versus expected 3.13; subsequent trajectory mismatches persist |

The corner and endpoint tests have no parameterized subtest contexts; their
case identification above follows the inspected fixture order and actual
values in the traceback. In particular the endpoint method aborts at e=0's
right-wall case; its later e=1 loop is **not** evidence of a pass during the
mutated run. Other tests independently exercised elastic impacts successfully.

### Secondary reporting and CLI failures

| Exact failing method | Failure entries | Explanation |
| --- | ---: | --- |
| `check_cli.CliChecks.test_headless_figures` | 1 | Expected CLI exit 0, observed 1. The report marks embedded integration/contact regressions failed; the short .2 s trajectory is not direct right-wall detection |
| `hw4.check_function_coverage.FunctionCoverageChecks.test_embedded_regression_report` | 1 | Expected passed=True and empty failures; embedded legacy contact assertions produce passed=False and failure details |
| `hw4.check_function_coverage.FunctionCoverageChecks.test_validation_failure_serialization_and_invalid_setup` | 1 | Final assertion `saved['regressions']['passed']` is false. Earlier invalid-setup and controlled plotting-error serialization assertions were reached successfully |

The full exact failure headers, including every reflection step, are extracted
without modification into
[mutated.failure_index.txt](bug_experiment/mutated.failure_index.txt).
Complete tracebacks remain in [mutated.stderr.txt](bug_experiment/mutated.stderr.txt).
There are 306 direct failure entries and 3 secondary entries, across seven
direct and three secondary methods. No secondary report failure is counted
as an independent physical oracle.

### Prediction comparison and informative passes

The set of 10 failing methods exactly matches the pre-mutation prediction.
The exact first divergent reflection step and count of cascading failures were
not predicted; observed divergence starts at step 103 and persists through 400.
The driver did not switch defects, modify tests, or retry with altered expectations.

All specifically predicted passing methods passed, including:

- `hw4.check_analytical.AnalyticalChecks.test_aligned_elastic_wall_reflection`
  and `hw4.check_conservation.ConservationChecks.test_repeated_elastic_collisions`:
  multiplying by e=1 and omitting that multiplication are equivalent.
- `hw4.check_symmetry.SymmetryChecks.test_mass_invariance`: even the incorrect
  law remains independent of mass; both e=1 and e=.8 pairs agree.
- `check_contacts.ContactChecks.test_default_trajectory`: boundedness and
  occurrence of all surfaces survive the wrong inelastic speed.
- `hw4.check_limiting.LimitingChecks.test_approach_to_zero_restitution`:
  the changed branch is the right wall, while this fixture hits only the floor.
- `hw4.check_function_coverage.FunctionCoverageChecks.test_bouncing_report_independent_first_impact_accounting`:
  its six-step fixture ends before the right-wall event.

The elastic subcase of `test_colliding_horizontal_reflection` also completed
without a failure. Contact-free analytical, conservation, convergence, limiting,
and scheduler tests passed. These passes demonstrate why physical response
assertions and multiple complementary properties are needed: passing one
invariant does not establish that every collision law is correct. No unexpected
test or execution failure occurred beyond the authorized defect's detections.

## Evidence and commands

All evidence is under [bug_experiment/](bug_experiment/). For **each** of
`baseline`, `mutated`, and `restored`, the four separate files
`<phase>.command.txt`, `<phase>.stdout.txt`, `<phase>.stderr.txt`, and
`<phase>.exit.txt` contain the working directory/exact command, complete raw
stdout, complete raw stderr, and process exit code. They were written directly
from subprocess streams, not copied from a truncated tool display.

The orchestrator was executed with these commands (both driver exits were 0):

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B hw4/bug_experiment/experiment_driver.py baseline
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B hw4/bug_experiment/experiment_driver.py experiment
```

The experiment driver's exit 0 reports successful restoration and verification;
the **mutated suite itself exited 1**, independently recorded. The interpreter
needed sandbox escalation; no dependency installation or version change occurred.

Additional evidence:

- `predictions.before_mutation.md`: exact pre-mutation report snapshot.
- `contacts.py.before`: original production bytes, not git HEAD contents.
- `intentional_bug.patch` and `mutation.json`: minimal edit and before/mutated
  SHA-256 hashes.
- `restoration.json`: byte equality, original/restored hashes, no execution error.
- `protected.before.json` and `protected.after.json`: unchanged protected-file
  hashes, including production code, tests, runner, SPEC and historical reports.
- `summary.json`: mutated/restored exits and protected-file equality.
- `baseline.git_status.txt`: starting changes, retained rather than reset.
- `final_diff_check.txt`: `git diff --check` returned 0. Separate no-index
  checks found no whitespace diagnostics in the new report/driver and HW4 README;
  raw captured streams and the exact source backup were not normalized.

## Restoration and limitations

The `finally` block restored the saved bytes before the final suite ran.
Byte equality is true, and both original/restored SHA-256 values are:

```text
8bd5b8679f8bda7739382f53996d37180e0400713759b0ff941b0a857e062fb7
```

All protected hashes match, and `git diff -- contacts.py` is empty. The restored
58-test suite passed in a fresh process with exit 0. No intentional defect
remains in production. Tests and SPEC are unchanged; all earlier reports,
including their historical pending-work statements, are preserved.

Only one controlled right-wall defect was evaluated. This establishes detection
of that defect, not a mutation score or proof that all possible defects are
detected. Failing subtests can prevent later assertions within that subtest from
running; the energy test's first detection is its velocity law. Native GUI and
plot visual fidelity were not evaluated. Outputs from the test suite were
temporary/headless. No interruption occurred; `try/finally` handles ordinary
exceptions/interruption but cannot guarantee recovery after forced process
termination or machine power loss. The exact backup remains available.

Changed deliverables for this experiment are this report, the new
`hw4/bug_experiment/` evidence/driver files, and report links/status in both
READMEs. Existing user changes were preserved. No personal narrative,
fabricated transcript reference, commit, or push was created.
