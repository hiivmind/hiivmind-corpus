"""Tests for detect.py — fastembed + lancedb availability detection."""
import subprocess
import sys

import pytest

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


class TestCachePathAndUv:
    """FASTEMBED_CACHE_PATH override and uv-aware availability."""

    def _run(self, env_overrides, tmp_path):
        import os
        env = os.environ.copy()
        env.update(env_overrides)
        return subprocess.run(
            [sys.executable, "lib/corpus/scripts/detect.py"],
            capture_output=True, text=True, env=env,
        )

    def test_custom_cache_path_with_model_reports_ready(self, tmp_path):
        """A bge-small model dir under FASTEMBED_CACHE_PATH must be found."""
        cache = tmp_path / "custom-cache"
        (cache / "models--qdrant--bge-small-en-v1.5").mkdir(parents=True)
        result = self._run({"FASTEMBED_CACHE_PATH": str(cache)}, tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == "ready"

    def test_custom_cache_path_empty_reports_no_model(self, tmp_path):
        cache = tmp_path / "empty-cache"
        cache.mkdir()
        result = self._run({"FASTEMBED_CACHE_PATH": str(cache)}, tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == "no-model"

    def test_uv_present_never_reports_not_installed(self, tmp_path, monkeypatch):
        """With uv on PATH, availability is guaranteed by `uv run`, so the
        import probe must be skipped even in an env without fastembed."""
        import shutil
        if shutil.which("uv") is None:
            pytest.skip("uv not installed on this host")
        cache = tmp_path / "empty-cache"
        cache.mkdir()
        # Run under the system python even if fastembed IS importable here;
        # the assertion is only that exit code is 0 and output is a model status.
        result = self._run({"FASTEMBED_CACHE_PATH": str(cache)}, tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() in ("ready", "no-model")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
