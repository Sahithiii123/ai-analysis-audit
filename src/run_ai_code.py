"""Run pasted model code once in a no-network Docker sandbox."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
import subprocess
import sys
import traceback
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from ai_output_utils import extract_prompt, extract_python_code, extract_response

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    "01_bank_marketing",
    "02_telco_churn",
    "03_olist_delivery_reviews",
    "04_simpsons_paradox",
    "05_multiple_comparisons",
    "06_iris_control",
)
IMAGE = "ai-analysis-audit-sandbox:latest"
DEFAULT_TIMEOUT = 300


@dataclass
class AttemptResult:
    attempt: int
    exit_code: int | None
    timed_out: bool
    timeout_seconds: int
    workspace: str


def write_launcher(path: Path) -> None:
    path.write_text(
        """from __future__ import annotations
import runpy
import sys
import traceback
from pathlib import Path

workspace = Path('/workspace')
try:
    runpy.run_path(str(workspace / 'pasted_code.py'), run_name='__main__')
except BaseException:
    traceback.print_exc()
    sys.exit(1)
finally:
    try:
        import matplotlib.pyplot as plt
        figure_dir = workspace / 'figures'
        figure_dir.mkdir(exist_ok=True)
        for number in plt.get_fignums():
            figure = plt.figure(number)
            figure.savefig(figure_dir / f'figure-{number:03d}.png', bbox_inches='tight')
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
""",
        encoding="utf-8",
    )


def docker_mount(path: Path, target: str, *, read_only: bool = False) -> str:
    source = path.resolve().as_posix()
    mode = ",readonly" if read_only else ""
    return f"type=bind,source={source},target={target}{mode}"


def run_attempt(
    *,
    docker: str,
    case: str,
    data_dir: Path,
    code: str,
    attempt: int,
    run_dir: Path,
    timeout_seconds: int,
) -> AttemptResult:
    workspace = run_dir / f"attempt-{attempt}"
    workspace.mkdir(parents=True, exist_ok=False)
    (workspace / "pasted_code.py").write_text(code, encoding="utf-8", newline="")
    write_launcher(workspace / "launcher.py")
    figures = workspace / "figures"
    figures.mkdir()

    container_name = f"ai-audit-{case.replace('_', '-')}-{attempt}-{datetime.now(UTC):%H%M%S%f}"
    command = [
        docker,
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        "none",
        "--read-only",
        "--memory",
        "2g",
        "--cpus",
        "1",
        "--pids-limit",
        "128",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=128m,mode=1777",
        "--mount",
        docker_mount(workspace, "/workspace"),
        "--mount",
        docker_mount(data_dir / "raw", "/workspace/data/raw", read_only=True),
        "--workdir",
        "/workspace",
        "--env",
        "MPLBACKEND=Agg",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        IMAGE,
        "python",
        "/workspace/launcher.py",
    ]
    metadata: dict[str, Any] = {
        "case": case,
        "attempt": attempt,
        "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "timeout_seconds": timeout_seconds,
        "network": "none",
        "sandbox_image": IMAGE,
    }
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        (workspace / "stdout.txt").write_bytes(completed.stdout)
        (workspace / "stderr.txt").write_bytes(completed.stderr)
        result = AttemptResult(
            attempt,
            completed.returncode,
            False,
            timeout_seconds,
            str(workspace),
        )
    except subprocess.TimeoutExpired as error:
        (workspace / "stdout.txt").write_bytes(error.stdout or b"")
        (workspace / "stderr.txt").write_bytes(error.stderr or b"")
        subprocess.run(
            [docker, "rm", "--force", container_name],
            capture_output=True,
            timeout=30,
            check=False,
        )
        result = AttemptResult(attempt, None, True, timeout_seconds, str(workspace))

    metadata.update(asdict(result))
    metadata["finished_at_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
    (workspace / "run.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=CASES)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--repair-source",
        type=Path,
        help="one manually prepared minimal repair file; tried only if the original crashes",
    )
    parser.add_argument("--image", default=IMAGE)
    arguments = parser.parse_args()
    if arguments.timeout < 1:
        parser.error("--timeout must be at least one second")

    docker = shutil.which("docker")
    if docker is None:
        print(
            "Refusing to execute pasted code: Docker is unavailable; "
            "no-network isolation cannot be guaranteed.",
            file=sys.stderr,
        )
        return 2

    load_dotenv(ROOT / ".env")
    configured_data_dir = Path(os.getenv("DATA_DIR", "data"))
    data_dir = (
        configured_data_dir
        if configured_data_dir.is_absolute()
        else ROOT / configured_data_dir
    )
    if arguments.image != IMAGE:
        print(
            f"Configured sandbox image must be {IMAGE!r}; custom images are not accepted.",
            file=sys.stderr,
        )
        return 2
    image_check = subprocess.run(
        [docker, "image", "inspect", IMAGE],
        capture_output=True,
        check=False,
    )
    if image_check.returncode != 0:
        print(
            f"Sandbox image {IMAGE!r} is missing. Build it with: "
            "docker build --tag ai-analysis-audit-sandbox:latest -f sandbox/Dockerfile .",
            file=sys.stderr,
        )
        return 2

    record_path = ROOT / "cases" / arguments.case / "ai_output" / "PASTE_HERE.md"
    prompt_path = ROOT / "cases" / arguments.case / "ai_output" / "PROMPT_TO_PASTE.md"
    record = record_path.read_text(encoding="utf-8")
    try:
        if extract_prompt(record) != prompt_path.read_text(encoding="utf-8").strip():
            raise ValueError("pasted prompt differs from the committed prompt")
        original_code = extract_python_code(extract_response(record))
    except ValueError as error:
        print(f"Output validation failed: {error}", file=sys.stderr)
        return 2

    run_root = ROOT / "reports" / "ai_code_runs" / arguments.case
    run_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = run_root / run_id
    run_dir.mkdir()
    (run_dir / "original_output.md").write_bytes(record_path.read_bytes())
    (run_dir / "original_code.py").write_text(original_code, encoding="utf-8", newline="")

    original = run_attempt(
        docker=docker,
        case=arguments.case,
        data_dir=data_dir,
        code=original_code,
        attempt=1,
        run_dir=run_dir,
        timeout_seconds=arguments.timeout,
    )
    summary: dict[str, Any] = {
        "case": arguments.case,
        "original": asdict(original),
        "repair": None,
        "finding": None,
    }

    if original.timed_out or original.exit_code != 0:
        summary["finding"] = {
            "type": "execution_failure",
            "attempt": 1,
            "message": (
                "Original pasted code did not complete successfully; "
                "see attempt-1/stderr.txt."
            ),
        }
        if arguments.repair_source is not None:
            repaired_code = arguments.repair_source.read_text(encoding="utf-8")
            if repaired_code == original_code:
                print(
                    "Repair source is identical to the original; refusing a no-op repair.",
                    file=sys.stderr,
                )
                return 2
            diff = difflib.unified_diff(
                original_code.splitlines(keepends=True),
                repaired_code.splitlines(keepends=True),
                fromfile="original_code.py",
                tofile="repaired_code.py",
            )
            diff_text = "".join(diff)
            (run_dir / "repair.diff").write_text(diff_text, encoding="utf-8", newline="")
            (run_dir / "repaired_code.py").write_text(repaired_code, encoding="utf-8", newline="")
            repaired = run_attempt(
                docker=docker,
                case=arguments.case,
                data_dir=data_dir,
                code=repaired_code,
                attempt=2,
                run_dir=run_dir,
                timeout_seconds=arguments.timeout,
            )
            summary["repair"] = asdict(repaired)
            summary["finding"]["repair_attempt"] = 2
            summary["finding"]["repair_exit_code"] = repaired.exit_code
            summary["finding"]["repair_timed_out"] = repaired.timed_out

    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Run artifacts: {run_dir.relative_to(ROOT)}")
    if summary["finding"] is not None:
        print(
            "Execution failure recorded as a finding; original code was preserved.",
            file=sys.stderr,
        )
        return 1
    print("Pasted code completed successfully in the no-network sandbox.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise