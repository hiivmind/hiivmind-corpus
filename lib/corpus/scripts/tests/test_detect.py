"""Tests for detect.py — fastembed + lancedb availability detection."""
import subprocess
import sys

SCRIPT = "lib/corpus/scripts/detect.py"


def run_detect():
    """Run detect.py and return (stdout, exit_code)."""
    result = subprocess.run(
        [sys.executable, SCRIPT],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.returncode


def test_output_is_single_line():
    """detect.py should output exactly one line."""
    stdout, _ = run_detect()
    lines = stdout.strip().split("\n")
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}: {lines}"


def test_output_is_valid_status():
    """Output must be one of the three valid statuses."""
    stdout, _ = run_detect()
    assert stdout in ("ready", "no-model", "not-installed"), (
        f"Unexpected output: {stdout}"
    )


def test_exit_code_matches_output():
    """Exit 0 for ready/no-model, exit 1 for not-installed."""
    stdout, code = run_detect()
    if stdout == "not-installed":
        assert code == 1, f"Expected exit 1 for not-installed, got {code}"
    else:
        assert code == 0, f"Expected exit 0 for {stdout}, got {code}"


def test_no_stderr_on_success():
    """detect.py should not write to stderr during normal operation."""
    result = subprocess.run(
        [sys.executable, SCRIPT],
        capture_output=True,
        text=True,
    )
    # stderr should be empty unless there's an error (exit 2)
    if result.returncode != 2:
        assert result.stderr == "", f"Unexpected stderr: {result.stderr}"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
