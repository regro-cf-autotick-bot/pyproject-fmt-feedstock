import sys
from subprocess import call
import site
from pathlib import Path
from typing import Any
from argparse import ArgumentParser

try:
    __import__("abi3audit")
    IS_ABI3 = True
except ImportError:
    IS_ABI3 = False


WIN = sys.platform == "win32"
SP_DIR = Path(site.getsitepackages()[-1])
PKG_SP_DIR = SP_DIR / "pyproject_fmt"
ABI3_EXT = "*.pyd" if WIN else "*.abi3.so"

FAIL_UNDER = "81"
COV = ["coverage"]
RUN = ["run", "--source=pyproject_fmt", "--branch", "-m"]
PYTEST = ["pytest", "pyproject-fmt/tests", "-vv", "--color=yes", "--tb=long"]
REPORT = ["report", "--show-missing", "--skip-covered", f"--fail-under={FAIL_UNDER}"]

SKIPS = [
    "classifier_gt_tox",
    # python-specific diff output in fixture?
    "(main and (format-cwd-no_check-in_place or format-absolute-no_check-in_place))",
    # works but throws instead of rc=1
    "invalid_project_version",
]

if WIN:
    SKIPS += [
        "help_invocation_as_script",
        "cli_pyproject_toml_not_file",
    ]

SKIP_OR = " or ".join(SKIPS)
K = ["-k", f"not ({SKIP_OR})"]


def do(*args: Any) -> int:
    """Condition and print arguemnts, return rc."""
    args = tuple(map(str, args))
    print(">>>", " \\\n\t".join(args), flush=True)
    return call(args)


def check_abi(python_min: str) -> int:
    """Maybe run abi3audit on all ``.pyd/.abi3.so``."""
    if not IS_ABI3:
        print("... abi3audit not available, skipping")
        return 0
    bins = sorted(PKG_SP_DIR.rglob(ABI3_EXT))
    if not bins:
        print(f"!!! no `{ABI3_EXT}` found in: {PKG_SP_DIR}")
        return 1
    return do("abi3audit", "-s", "-v", "--assume-minimum-abi3", python_min, *bins)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--python-min")
    ns = parser.parse_args()
    sys.exit(
        check_abi(python_min=ns.python_min)
        # run the tests
        or do(*COV, *RUN, *PYTEST, *K)
        # maybe run coverage
        or do(*COV, *REPORT)
    )
