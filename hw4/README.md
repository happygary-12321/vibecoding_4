# HW4 physics tests and function coverage

This folder contains independent analytical tests for the simulator's supported
2D translational physics, using the existing standard-library `unittest`
framework. The simulator source files remain in the repository root.

Run the **complete HW4 + legacy suite** from the repository root:

```powershell
python -B -m hw4.run_tests
```

Exact command used on this machine:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
```

[run_tests.py](run_tests.py) explicitly includes every `check_*.py` in the
repository root and `hw4/`, rather than relying on unittest's `test*.py`
default pattern. It prints included modules/counts, returns nonzero for test
failures or import errors, and rejects empty test modules. No dependencies or
failed imports are silently skipped. The complete suite requires the plotting
dependencies used by the legacy CLI smoke test (`requirements-figures.txt`);
that test uses Agg and a temporary directory. No native GUI is launched.

- [function_coverage.md](function_coverage.md): production inventory mapped to
  exact tests, assertions, direct/indirect coverage, and explicit remaining gaps.
- [coverage_results.md](coverage_results.md): agent-generated audit results,
  initial test error and correction, commands, changed files, and limitations.
- [check_function_coverage.py](check_function_coverage.py): 18 additional tests
  for validation/evidence, scheduler boundaries, CLI/GUI orchestration, and
  runner behavior. Run alone with `python -B -m hw4.check_function_coverage`.
  Completion checks also verify cumulative discard across repeated overloads
  and side-wall contacts above the displayed wall height. The complete suite
  contains 58 test methods; see the coverage report for the latest execution.

- [check_analytical.py](check_analytical.py): upward launch through the apex,
  checking the exact solution and signed Euler height bias across two entry
  points, two timesteps, and two masses; and a gravity-free elastic wall
  reflection at two timesteps aligned with impact. Two tests cover ten
  parameter combinations and check every timestep.
- [step1_results.md](step1_results.md): agent-generated factual report with
  assumptions, derivations, tolerances, commands, and results. It is not the
  user's personal testing log.
- [check_conservation.py](check_conservation.py): four Part 2 tests for
  gravity-free momentum and kinetic-energy conservation, repeated elastic
  impacts, inelastic energy balance, and the production energy helper.
- [step2_results.md](step2_results.md): agent-generated Part 2 rationale,
  tolerance analysis, commands, and results; not a personal testing log.

- [check_convergence.py](check_convergence.py): Part 3 first-order convergence
  of uncorrected vertical-position error over four timesteps at a shared
  endpoint time, for both integration entry points.
- [step3_results.md](step3_results.md): agent-generated derivation, tolerance
  rationale, measured errors/ratios/orders, commands, and results.

- [check_symmetry.py](check_symmetry.py): Part 4 horizontal reflection of
  free flight and elastic/inelastic collisions, plus mass invariance with
  gravity and collisions. Contacts are matched by surface identity.
- [step4_results.md](step4_results.md): agent-generated symmetry derivations,
  fixture/tolerance rationale, measured residuals, contact counts, and results.

- [check_limiting.py](check_limiting.py): Part 5 zero-gravity position evolution,
  stationary motion, e=0 collisions/follow-up, and approach to zero restitution.
- [step5_results.md](step5_results.md): agent-generated limiting-case references,
  tolerance rationale, measurements, commands, results, and remaining work.

From the `HW3_submission` root, run an individual part or all five:

```powershell
python -B -m hw4.check_analytical
python -B -m hw4.check_conservation
python -B -m hw4.check_convergence
python -B -m hw4.check_symmetry
python -B -m hw4.check_limiting
python -B -m unittest -v hw4.check_analytical hw4.check_conservation hw4.check_convergence hw4.check_symmetry hw4.check_limiting
```

Parts 1–5 only, excluding the audit additions and legacy suites:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v hw4.check_analytical hw4.check_conservation hw4.check_convergence hw4.check_symmetry hw4.check_limiting
```

Use module execution from the root so `integration`, `state`, and `contacts`
remain importable without copying source files or modifying the import path.
The HW4 suites were tested on CPython 3.12.10 (64-bit Windows); none imposes
an exact patch-version restriction. SPEC describes such guards in the four
legacy scripts but does not require them for HW4. The Part 1 guard was removed
in Part 2; the Part 1 report retains its historical verification record.
No other interpreter version was tested. Parts 1–5 alone need no GUI or plotting
dependencies. The complete runner also includes the legacy suites and their
headless plotting smoke test. Figure generation still embeds only the legacy
integration/contact suites. Rotation is outside the simulator's model.

The Part 2 trajectory cases use zero gravity. Fixed walls exchange momentum
with the circle, so only free-flight particle momentum is conserved. Without
gravity or a ceiling, each trajectory can hit the floor only once; two elastic
launches each test that floor impact and repeated impacts on both side walls.
Inelastic cases check energy loss, not conservation. No test requires exact
mechanical-energy conservation for semi-implicit Euler under gravity.

Part 3 measures `abs(y_numeric(T)-y_exact(T))` without bias correction at
T=1.5 s, using 24, 48, 96, and 192 steps. It checks monotone error decrease
and `log2(E_coarse/E_fine)` within 1e-9 of 1. Horizontal position and both
velocities are checked separately at roundoff tolerance. Passing this
smooth-flight test does not establish convergence order across collisions.
Earlier reports remain unchanged as historical records.

Part 4 checks `(x,y,vx,vy) -> (W-x,y,-vx,vy)` and mass-independent motion.
Normal contact velocities are invariant under reflection; corrections transform
as `(dx,dy) -> (-dx,dy)`. Fixtures exclude corner contacts and near-threshold
contact ambiguity. No vertical-reflection, fixed-wall translation, or time-
reversibility claim is made. Momentum and energy are not mass-invariant.

Part 5 follows SPEC's stationary-touch records after e=0 impacts. Its positive
small-e speed and normal-energy comparisons use relative-only tolerances and
strict positivity, preventing a zeroed response from passing. It introduces no
new resting-contact model and uses only supported parameter values.

The major-function audit is complete for the documented simulator scope; native
GUI and plot visual-fidelity gaps remain explicitly identified in the audit.
The authorized [intentional-bug experiment](bug_experiment_results.md) is complete:
58 tests passed before and after exact production restoration; the temporary
right-wall defect caused 10 methods to fail (309 failure entries), exit 1.
Raw evidence is in [bug_experiment/](bug_experiment/).
The user's personally written log and reviewed git commits remain pending.
Earlier step reports preserve their historical status; the coverage report
records the current audit outcome.
