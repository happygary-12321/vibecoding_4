# HW4 major-function coverage audit

Agent-generated audit of meaningful assertions, not a line-coverage report or
the user's personal log. Read alongside [coverage_results.md](coverage_results.md).
The complete-suite command is `python -B -m hw4.run_tests` from the repository
root. All test names below refer to cases included by that runner.

## Scope and classification

Production simulator scope follows SPEC section 6: `state`, `integration`,
`contacts`, `rendering`, `validation`, `cli`, `main`, and `make_figures`.
A major function implements physics, validates an input contract, controls time,
computes or reports numerical evidence, dispatches an entry point, or manages
visualization. Tiny policy/report helpers are included as minor functions so
they cannot disappear from the inventory. Nested callbacks are listed too.
Dataclass-generated constructors/equality/repr and inherited exception methods
are not handwritten production functions; their relevant observable behavior
is covered through constructors and post-init validation. `RenderingDependencyError`
is an exception marker with no custom method.

Excluded from the production simulator inventory:

- All `check_*.py` test classes/helpers and `hw4/run_tests.py` test infrastructure.
- Generated data, figures, report artifacts, and historical copied evidence.
- Repository maintenance tools: `build_report.main` and its nested `literal`,
  `flush`, `footer`; `final_verify.main`; `package_submission.git/main`;
  `preserve_transcript.main`. They build/archive/audit earlier assignment
  submissions or export transcripts, and are not called by the simulator.
  They are present in this checkout despite historical absence notes in SPEC.
  This audit makes no coverage claim for those tools and did not execute them.

Direct means the test calls the function/method under audit. Indirect means it
is reached through a tested public operation and assertions actually constrain
its behavior. Merely constructing an object or executing a line is not counted
as behavioral verification. A test with a mocked callee covers the caller's
dispatch, not the mocked callee's implementation.

## Physics and state inventory

| Module and function/method | Responsibility; major? | Exact associated tests | What is asserted | Direct/indirect | Gap and disposition |
| --- | --- | --- | --- | --- | --- |
| `integration.step` | Velocity-first update and count; **yes** | `check_integration.IntegrationChecks.test_one_step`; `hw4.check_analytical.AnalyticalChecks.test_upward_launch_through_apex`; `hw4.check_convergence.ConvergenceChecks.test_first_order_smooth_flight`; `hw4.check_limiting.LimitingChecks.test_zero_gravity_uniform_motion` | Independent one-step values, ascent/apex/descent, signed bias, first-order error over four h, uniform positions and velocities | Direct | Adequate; reused without duplicate integrator tests |
| `integration.complete_step` | Validate geometry, integrate, then resolve; **yes** | `check_contacts.ContactChecks.test_complete_step_order`; `hw4.check_symmetry.SymmetryChecks.test_colliding_horizontal_reflection`; `hw4.check_function_coverage.FunctionCoverageChecks.test_invalid_geometry_rejected_before_mutation` | Gravity precedes response, corner outcomes/count/order, mapped contacts, unchanged state on invalid geometry | Direct | Added rejection-before-mutation check; prior physical cases retained |
| `contacts.resolve_contacts` | Radius projection, direction guards, restitution, records; **yes** | `check_contacts.ContactChecks.test_surfaces_and_directions`; `check_contacts.ContactChecks.test_both_corners`; `check_contacts.ContactChecks.test_restitution_endpoints`; `check_contacts.ContactChecks.test_no_contact_and_no_ceiling`; `hw4.check_function_coverage.FunctionCoverageChecks.test_invalid_geometry_rejected_before_mutation`; `hw4.check_limiting.LimitingChecks.test_zero_restitution_impact_and_followup` | All surfaces, touching/penetration, inward/outgoing/zero normal velocity, tangent/count preservation, floor-first corners, endpoints e=0/1, no ceiling, atomic rejection, 20 stationary-touch follow-ups | Direct legacy/new geometry; indirect via complete steps for limits | Added atomic geometry rejection; existing surface tests reused |
| `contacts.ContactRecord.is_impact` | Normal velocity-change flag; **yes**, observable contact classification | `check_contacts.ContactChecks.test_surfaces_and_directions`; `hw4.check_limiting.LimitingChecks.test_zero_restitution_impact_and_followup`; `hw4.check_limiting.LimitingChecks.test_approach_to_zero_restitution` | Changed velocities are impacts; outgoing/zero-speed records are not; e=0 first impact differs from subsequent touches | Direct property reads | Small-e test additionally checks recorded pre/post velocities against independent values and actual state, including e=0 |
| `state._finite` | Reject nonnumeric/bool/nonfinite fields; **yes**, shared validation | `check_integration.IntegrationChecks.test_invalid_state_and_parameters`; `hw4.check_function_coverage.FunctionCoverageChecks.test_state_type_validation_and_mutation` | NaN/inf rejected across fields; bool/string/None rejected through representative state, parameter, and box fields | Indirect through constructors/validate | Added type rejection; arbitrary huge integers that overflow math.isfinite remain a documented limitation |
| `state.PhysicsParameters.__post_init__` | Physical parameter ranges; **yes** | `check_integration.IntegrationChecks.test_defaults_and_geometry`; `check_integration.IntegrationChecks.test_invalid_state_and_parameters`; `hw4.check_function_coverage.FunctionCoverageChecks.test_state_type_validation_and_mutation` | Defaults; positive mass/radius/h; nonnegative gravity; restitution [0,1]; nonfinite and unsupported types rejected | Indirect constructor | Adequate ranges reused; type cases added |
| `state.Box.__post_init__` | Finite positive dimensions; **yes** | `check_integration.IntegrationChecks.test_invalid_state_and_parameters`; `hw4.check_function_coverage.FunctionCoverageChecks.test_state_type_validation_and_mutation` | Nonpositive/nonfinite dimensions and unsupported types rejected | Indirect constructor | Type gap added; no new geometry rules |
| `state.Box.validate_for` | Both dimensions strictly exceed diameter; **yes** | `check_integration.IntegrationChecks.test_defaults_and_geometry`; `hw4.check_function_coverage.FunctionCoverageChecks.test_invalid_geometry_rejected_before_mutation` | Legal box accepted; undersized/equal-diameter boxes rejected for width and height; complete-step/resolver/scheduler rejection | Direct legacy; indirect new | Added both exact diameter boundaries and rejection before state mutation |
| `state.CircleState.__post_init__` | Invoke state validation; **minor** delegator | `check_integration.IntegrationChecks.test_invalid_state_and_parameters`; `hw4.check_function_coverage.FunctionCoverageChecks.test_state_type_validation_and_mutation` | Bad state/count fails construction; finite outside-box positions remain legal numerical data | Indirect constructor | Adequate; no separate wrapper-only duplicate |
| `state.CircleState.validate` | Revalidate mutable fields/count; **yes** | `check_integration.IntegrationChecks.test_invalid_state_and_parameters`; `hw4.check_function_coverage.FunctionCoverageChecks.test_state_type_validation_and_mutation`; `hw4.check_function_coverage.FunctionCoverageChecks.test_invalid_geometry_rejected_before_mutation` | Reject mutation to NaN/bool/negative count, accept legal exterior coordinates without mutation, scheduler rejects invalid mutable state | Direct and indirect | Added post-construction mutation checks |
| `state.CircleState.time` | Reconstruct count*h seconds; **yes** | `check_integration.IntegrationChecks.test_one_step`; `hw4.check_function_coverage.FunctionCoverageChecks.test_state_type_validation_and_mutation`; `hw4.check_function_coverage.FunctionCoverageChecks.test_sample_is_independent_snapshot` | Count 8 at h=.1 gives .8; count 7 at h=.125 gives .875 without changing state | Direct and indirect via sample | Adequate; fixed-h assumption preserved |

## Scheduling, CLI, and entry points

Completion review adds the following precise associations to the inventory:

| Module and function/method | Responsibility; major? | Exact associated test | What is asserted | Direct/indirect | Gap and disposition |
| --- | --- | --- | --- | --- | --- |
| `contacts.resolve_contacts` | Side-wall response without height cutoff; **yes** | `hw4.check_function_coverage.FunctionCoverageChecks.test_side_walls_above_displayed_height` | At y=8 above H=3, both walls project by signed .125 m, change inward normal -3 to +1.5, preserve y/vy/count, and emit exactly the expected impact record | Direct | Added explicit above-height contacts; existing no-ceiling test only checks interior x |
| `rendering.FixedStepScheduler.advance` | Cumulative overload bookkeeping; **yes** | `hw4.check_function_coverage.FunctionCoverageChecks.test_repeated_overload_accumulates_discarded_time` | Execute 60,60,1,0 steps from initial count 7; cumulative dropped counts 10,30,30,30; exact elapsed/remainder/discard balance and independent positions after every call | Direct | Added two successive overloads so replacing cumulative counters with per-call values cannot pass; zero elapsed cannot replay discarded backlog |

| Module and function/method | Responsibility; major? | Exact associated tests | What is asserted | Direct/indirect | Gap and disposition |
| --- | --- | --- | --- | --- | --- |
| `rendering.FixedStepScheduler.__post_init__` | Validate initial state and geometry; **yes** | `hw4.check_function_coverage.FunctionCoverageChecks.test_invalid_geometry_rejected_before_mutation` | Reject equal-diameter geometry and an infinite velocity introduced after state construction | Indirect constructor | Added rejection behavior; successful construction alone was insufficient |
| `rendering.FixedStepScheduler.advance` | Fixed-step accumulation, snapping, cap/discard; **yes** | `check_scheduling.SchedulingChecks.test_insufficient_and_fractional_time`; `check_scheduling.SchedulingChecks.test_display_interval_independence`; `check_scheduling.SchedulingChecks.test_cap_discard_and_remainder`; `check_scheduling.SchedulingChecks.test_exact_cap_does_not_discard`; `check_scheduling.SchedulingChecks.test_invalid_elapsed`; `hw4.check_function_coverage.FunctionCoverageChecks.test_scheduler_rounding_physics_and_overflow` | Actual counts/remainders; 240 equal steps across schedules; 60-step cap plus 65 dropped steps; invalid elapsed; 4-ulp snap vs 16-ulp floor; independent x/y displacement, elapsed counters, follow-up fractional accumulation; quotient overflow rejected without mutation | Direct | Added rounding branches, physical displacement, overflow; reused backlog tests |
| `cli.finite_number` | Numeric string conversion/nonfinite rejection; **yes** | `check_cli.CliChecks.test_invalid_inputs`; `check_cli.CliChecks.test_main_passes_parameters_without_opening_gui` | Malformed/nonfinite values exit 2; decimal/scientific inputs become expected numeric parameters | Indirect through parser/entry point | Adequate; no duplicate validator tests |
| `cli.restitution_value` | Inclusive [0,1] argument; **yes** | `check_cli.CliChecks.test_invalid_inputs`; `check_cli.CliChecks.test_main_passes_parameters_without_opening_gui` | Out-of-range failure and valid 0,1,.25 dispatch | Indirect | Adequate |
| `cli.timestep_value` | Positive finite timestep; **yes** | `check_cli.CliChecks.test_invalid_inputs`; `check_cli.CliChecks.test_main_passes_parameters_without_opening_gui` | Zero/negative/nonfinite reject; 1e-3 and .02 parsed and forwarded correctly | Indirect | Adequate |
| `cli.parse_args` | Shared/figure options, help and experiment validation; **yes** | `check_cli.CliChecks.test_defaults`; `check_cli.CliChecks.test_figure_options`; `check_cli.CliChecks.test_help`; `check_cli.CliChecks.test_missing_values`; `hw4.check_function_coverage.FunctionCoverageChecks.test_figure_entry_dispatch_and_failures` | Default values, figure constraints, help status/text, missing-value errors, custom output/duration/bounce/restitution/h forwarded exactly | Direct and indirect | Reused valid/invalid parser cases; added full figure dispatch assertions |
| `main.main` | Parse, construct physics, launch GUI adapter, exit/error policy; **yes** | `check_cli.CliChecks.test_main_passes_parameters_without_opening_gui`; `check_cli.CliChecks.test_main_help_and_invalid_args_do_not_import_rendering`; `check_cli.CliChecks.test_main_dependency_message_and_unexpected_errors` | Numeric parameters and return 0, parsing before rendering import, dependency message/status 1, unexpected errors propagate | Direct, mocked launch | Adequate caller coverage; mocks are not native GUI verification |
| `make_figures.main` | Headless dispatch and success/failure status; **yes** | `check_cli.CliChecks.test_headless_figures`; `check_cli.CliChecks.test_help`; `hw4.check_function_coverage.FunctionCoverageChecks.test_figure_entry_dispatch_and_failures` | Real successful subprocess writes expected artifacts and config; help exits; exact custom argument dispatch; failed report and OSError return 1 with meaningful diagnostics; unexpected ValueError propagates | Direct new; indirect subprocess legacy | Added error/dispatch cases; all outputs temporary |

## Numerical validation and evidence helpers

| Module and function/method | Responsibility; major? | Exact associated tests | What is asserted | Direct/indirect | Gap and disposition |
| --- | --- | --- | --- | --- | --- |
| `validation.whole_steps` | Aligned duration-to-count conversion and work bounds; **yes** | `check_cli.CliChecks.test_figure_options`; `hw4.check_function_coverage.FunctionCoverageChecks.test_whole_steps_boundaries_and_rejections` | 1 and 1,000,000 accepted; >limit, <one step, nonpositive/nonfinite and quotient overflow rejected; 4 ulps accepted, 16 ulps rejected | Direct new; indirect CLI | Added exact boundaries and near-integer acceptance policy |
| `validation.validate_experiments` | Coarse/fine/bounce counts and safe free fall; **yes** | `check_cli.CliChecks.test_figure_options`; `hw4.check_function_coverage.FunctionCoverageChecks.test_experiment_counts_and_discrete_floor_guard` | Counts (4,8,16), continuous floor rejection, stricter discrete floor rejection at h=T=1, fine-run work cap, nonaligned bounce duration | Direct new; indirect CLI | Added discrete-floor and fine-run limits; redundant fine!=2*coarse guard not artificially forced |
| `validation.tolerance` | Base versus roundoff-scale policy; **minor**, numerical acceptance support | `hw4.check_function_coverage.FunctionCoverageChecks.test_check_helpers_and_tolerance_policy` | Base-dominated value; scale floor 1; roundoff-dominated exact powers 2^-49 and 2^-29 | Direct | Added independent expected budgets; no longer only used as its own oracle |
| `validation.check_close` | Record finite absolute-residual pass/fail; **minor**, evidence policy | `hw4.check_function_coverage.FunctionCoverageChecks.test_check_helpers_and_tolerance_policy` | Inclusive +/- tolerance boundary, next representable value outside fails, NaN/inf fail, complete result fields | Direct | Added false outcomes and boundary checks |
| `validation.check_true` | Record boolean acceptance; **minor** | `hw4.check_function_coverage.FunctionCoverageChecks.test_check_helpers_and_tolerance_policy` | Empty/nonempty truth conversion and exact measured/expected/passed fields | Direct | Added true/false reporting checks |
| `validation.energy` | K+m*g*y; **yes** | `hw4.check_conservation.ConservationChecks.test_energy_helper_against_independent_values`; `hw4.check_function_coverage.FunctionCoverageChecks.test_sample_is_independent_snapshot` | Independent energies 31.25,80.3,49.05,0 J; nonunit mass and nonzero components/potential | Direct Part 2; indirect sample | Adequate; reused Part 2 |
| `validation.sample` | Detached state/time/energy dictionary; **yes**, evidence boundary | `hw4.check_function_coverage.FunctionCoverageChecks.test_sample_is_independent_snapshot` | Every field against an independent snapshot (time .875, energy 80.3), no state mutation, later state/dict edits do not alias | Direct | Added snapshot and value checks |
| `validation.free_fall` | Numerical/exact histories, errors, energy drift/checks; **yes** | `hw4.check_function_coverage.FunctionCoverageChecks.test_free_fall_report_against_independent_solution`; `check_cli.CliChecks.test_headless_figures` | Five samples for g=2,m=3,h=.125; independent y=10-n(n+1)/64, vy=-2t, exact height, signed error, E and drift=-3t/4; final matches last sample | Direct new; indirect CLI | Added independent history/energy assertions beyond self-reported passed flags |
| `validation.bouncing` | Contact history/counts and energy accounting; **yes** | `hw4.check_function_coverage.FunctionCoverageChecks.test_bouncing_report_independent_first_impact_accounting`; `check_cli.CliChecks.test_headless_figures` | First floor impact at step 5, vn=-2.5, correction .125 m, projection energy .75 J; e=.5 loss -7.03125 J versus e=1 loss 0; final state/energies 6.84375 or 13.875 J and integration drift -2.25 J | Direct new; indirect CLI | Added independent impact-present report check; legacy short .2 s smoke run does not hit floor |
| `validation.contact_direction` | Upward-overlap diagnostic report; **yes** | `hw4.check_function_coverage.FunctionCoverageChecks.test_contact_direction_report`; `check_cli.CliChecks.test_headless_figures` | y=.2, vy=+2 retained, no impact; illustrative scalar -1.6; all three check results | Direct new; indirect CLI | Added report value checks; illustrative scalar is existing production diagnostic, not injected code |
| `validation.regression_checks` | Run/capture integration and contact suites; **yes** | `hw4.check_function_coverage.FunctionCoverageChecks.test_embedded_regression_report`; `check_cli.CliChecks.test_headless_figures` | Exactly 11 embedded tests, passed flag and empty failure/error lists, output contains both test families and count | Direct new; indirect CLI | Added summary and captured-content assertions; embedded-suite failure serialization not exhaustively tested |
| `validation.run_validation` | Orchestrate experiments and persist report/status; **yes** | `check_cli.CliChecks.test_headless_figures`; `hw4.check_function_coverage.FunctionCoverageChecks.test_validation_failure_serialization_and_invalid_setup` | Real successful report and PNG outputs; invalid setup rejected before directory creation; controlled plot I/O error gives persisted failed status, traceback and empty figures, retains completed numerical histories | Direct new failure case; indirect real success subprocess | Added failure lifecycle; successful execution kept in clean subprocess because production rejects preloaded rendering modules |

## Visualization and GUI inventory (scope is deliberately explicit)

| Module and function/method | Responsibility; major? | Exact associated tests | What is asserted | Direct/indirect | Remaining scope |
| --- | --- | --- | --- | --- | --- |
| `validation.write_plots` | Agg plots and PNG artifacts from numerical report; **yes**, visualization | `check_cli.CliChecks.test_headless_figures` | Real headless backend=Agg, exact four filenames, PNG signatures, figure list/report output | Indirect through real headless subprocess | Meaningful artifact-generation test, not pixel/curve/label/layout verification; plot visual correctness remains unverified |
| `validation.write_plots.save` | Save/close a figure and append filename; **minor** nested helper | `check_cli.CliChecks.test_headless_figures` | All named PNGs actually exist with PNG headers and match report list | Indirect | File-writing behavior covered; figure closure is not separately observed, pixel quality not tested |
| `rendering.run_simulation` | Lazy dependency handling, scene/event-loop lifecycle; **yes**, GUI | `hw4.check_function_coverage.FunctionCoverageChecks.test_rendering_dependency_classification`; `hw4.check_function_coverage.FunctionCoverageChecks.test_rendering_callback_physics_and_cleanup` | PyVista/VTK dependency errors translated, unrelated ModuleNotFoundError propagated; real scheduler with fake backend; four physical steps produce actor (1.75,1.6875,0), status time .50, final count/time; failed timer prevents show; callback exception propagated; close on normal and both failure paths | Direct with fake backend | Meaningful application logic, **not native GUI integration**: mesh/camera pixels, real timer/input/close behavior and installed backend compatibility remain untested |
| `rendering.run_simulation.update` | Timer-to-scheduler advance, actor/status update, callback error transfer; **yes**, nested GUI callback | `hw4.check_function_coverage.FunctionCoverageChecks.test_rendering_callback_physics_and_cleanup` | First event starts clock; times 0,.25,.5 at h=.125 integrate exactly four real steps; independent endpoint and displayed time; render error terminates and is re-raised after loop | Indirect through callback registered by real run_simulation | Added actual physical state assertion, not callback-count-only mock; real event-loop timing remains unverified |

## Conclusion and remaining limitations

Every major function in the defined simulator inventory now has a meaningful
associated test, and adequate legacy tests are reused. This means a specified
observable behavior is verified; it does **not** mean every branch or input is
covered, nor is it a statement of measured line/branch coverage.

Explicit remaining gaps: native PyVista/VTK end-to-end rendering/input/lifecycle;
plot visual fidelity and plotted-series correspondence; exhaustive I/O failures
and every defensive branch; arbitrary extreme numerical inputs outside the
tested scale; maintenance/report-packaging tools outside simulator scope.
The SPEC's documented very-large-integer OverflowError behavior and lack of
resting/contact-time resolution are not changed. No new physical model is
introduced. GUI-associated tests are never described as a successful GUI run.

The runner itself is tested by
`hw4.check_function_coverage.FunctionCoverageChecks.test_runner_includes_both_directories_and_fails_closed`:
temporary root/HW4 `check_*.py` probes both execute; synthetic assertion failure
and synthetic import error each return exit 1. These probes are test-infrastructure
checks, not production defects or the pending intentional-bug experiment.
