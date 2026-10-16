"""Run every root and HW4 check_*.py suite; imports/errors must fail visibly.

From the repository root: python -B -m hw4.run_tests
Explicit file enumeration also works with HW4 as a namespace package.
"""

import importlib
from pathlib import Path
import sys
import unittest


def main():
    root = Path(__file__).resolve().parent.parent
    paths = sorted(root.glob("check_*.py")) + sorted((root / "hw4").glob("check_*.py"))
    if not paths:
        raise RuntimeError("No check_*.py suites found")
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    for path in paths:
        name = ".".join(path.relative_to(root).with_suffix("").parts)
        # Do not catch ImportError or missing dependencies: process must fail.
        tests = loader.loadTestsFromModule(importlib.import_module(name))
        if tests.countTestCases() == 0:
            raise RuntimeError(f"No unittest cases in {name}")
        print(f"Included {name}: {tests.countTestCases()} tests", flush=True)
        suite.addTests(tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
