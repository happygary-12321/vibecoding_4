"""Evidence capture for the explicitly authorized, single controlled defect.

Run baseline first, write predictions, then run experiment. Not a test suite.
"""

import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "contacts.py"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def protected_hashes():
    paths = set(ROOT.glob("*.py")) | set((ROOT / "hw4").glob("check_*.py"))
    paths |= set((ROOT / "hw4").glob("step*_results.md"))
    paths |= {ROOT / "assign3/SPEC.md", ROOT / "hw4/run_tests.py",
              ROOT / "hw4/function_coverage.md", ROOT / "hw4/coverage_results.md"}
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(paths)}


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run_suite(label):
    command = [sys.executable, "-B", "-m", "hw4.run_tests"]
    (OUT / f"{label}.command.txt").write_text(
        f"Working directory: {ROOT}\n" + subprocess.list2cmdline(command) + "\n",
        encoding="utf-8")
    with (OUT / f"{label}.stdout.txt").open("wb") as stdout, \
            (OUT / f"{label}.stderr.txt").open("wb") as stderr:
        try:
            result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                    timeout=180, check=False)
        except BaseException as exc:
            (OUT / f"{label}.execution_error.txt").write_text(repr(exc), encoding="utf-8")
            raise
    (OUT / f"{label}.exit.txt").write_text(str(result.returncode) + "\n", encoding="utf-8")
    print(f"{label}: exit {result.returncode}", flush=True)
    return result.returncode


def baseline():
    backup = OUT / "contacts.py.before"
    if backup.exists():
        raise RuntimeError("Existing baseline evidence must not be overwritten")
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT,
                            capture_output=True, check=True)
    (OUT / "baseline.git_status.txt").write_bytes(status.stdout)
    backup.write_bytes(SOURCE.read_bytes())
    save_json("protected.before.json", protected_hashes())
    return run_suite("baseline")


def experiment():
    if (OUT / "baseline.exit.txt").read_text().strip() != "0":
        raise RuntimeError("Passing baseline required")
    if (OUT / "mutated.command.txt").exists():
        raise RuntimeError("Existing mutation evidence must not be overwritten")
    before = (OUT / "contacts.py.before").read_bytes()
    if SOURCE.read_bytes() != before:
        raise RuntimeError("Production source changed after baseline; refusing mutation")
    if protected_hashes() != json.loads((OUT / "protected.before.json").read_text()):
        raise RuntimeError("Protected files changed after baseline")
    predictions = ROOT / "hw4/bug_experiment_results.md"
    (OUT / "predictions.before_mutation.md").write_bytes(predictions.read_bytes())
    old = b"if state.vx > 0:\n            state.vx = -restitution * state.vx"
    newline = b"\r\n" if b"\r\n" in before else b"\n"
    old = old.replace(b"\n", newline)
    new = old.replace(b"-restitution * state.vx", b"-state.vx")
    if before.count(old) != 1:
        raise RuntimeError("Expected exactly one right-wall response")
    after = before.replace(old, new, 1)
    patch = "".join(difflib.unified_diff(
        before.decode("utf-8").splitlines(keepends=True),
        after.decode("utf-8").splitlines(keepends=True),
        fromfile="a/contacts.py", tofile="b/contacts.py"))
    (OUT / "intentional_bug.patch").write_bytes(patch.encode("utf-8"))
    failure = None
    mutated_exit = None
    try:
        SOURCE.write_bytes(after)
        save_json("mutation.json", {"before_sha256": digest(before),
                                   "mutated_sha256": digest(SOURCE.read_bytes())})
        mutated_exit = run_suite("mutated")
    except BaseException as exc:
        failure = repr(exc)
    finally:
        SOURCE.write_bytes(before)
        equal = SOURCE.read_bytes() == before
        save_json("restoration.json", {"byte_equal": equal,
                  "before_sha256": digest(before),
                  "restored_sha256": digest(SOURCE.read_bytes()),
                  "experiment_execution_error": failure})
        if not equal:
            raise RuntimeError("Exact restoration failed")
    restored_exit = run_suite("restored")
    hashes = protected_hashes()
    save_json("protected.after.json", hashes)
    unchanged = hashes == json.loads((OUT / "protected.before.json").read_text())
    save_json("summary.json", {"mutated_exit": mutated_exit,
                              "restored_exit": restored_exit,
                              "protected_files_unchanged": unchanged,
                              "experiment_execution_error": failure})
    return 0 if restored_exit == 0 and unchanged and failure is None else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["baseline"]:
        raise SystemExit(baseline())
    if sys.argv[1:] == ["experiment"]:
        raise SystemExit(experiment())
    raise SystemExit("Specify baseline or experiment")
