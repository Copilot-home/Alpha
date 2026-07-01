#!/usr/bin/env python3
"""
End-to-end orchestration helper for multi-account AI-agent workflow.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_MAP_PATH = REPO_ROOT / ".github" / "orchestration" / "capability_map.json"
TASK_ROUTING_PATH = REPO_ROOT / ".github" / "orchestration" / "task_routing.yml"


ACCOUNT_MATRIX = {
    "gmail": {
        "email": "nguyencuong.2509@gmail.com",
        "token_env": "GITHUB_TOKEN_GMAIL",
    },
    "icloud": {
        "email": "nguyencuong.2509@icloud.com",
        "token_env": "GITHUB_TOKEN_ICLOUD",
    },
}


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    env = os.environ.copy()
    pythonpath_prefix = str(REPO_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{pythonpath_prefix}:{existing_pythonpath}"
        if existing_pythonpath
        else pythonpath_prefix
    )

    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    output = "\n".join(x for x in [stdout, stderr] if x)
    return proc.returncode, output


def validate_dr_protocol() -> dict:
    checks = [
        ["python", "-m", "py_compile", "src/hyperai/protocols/dr_protocol.py"],
        ["python", "-m", "compileall", "-q", "src/hyperai/protocols/dr_protocol.py"],
        [
            "python",
            "-c",
            "from hyperai.protocols.dr_protocol import DRProtocol; print(DRProtocol.__name__)",
        ],
    ]
    results = []
    ok = True
    for cmd in checks:
        code, output = run_cmd(cmd)
        passed = code == 0
        ok = ok and passed
        results.append(
            {
                "command": " ".join(cmd),
                "exit_code": code,
                "passed": passed,
                "output": output,
            }
        )
    return {"passed": ok, "checks": results}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_task_routes(path: Path) -> dict:
    # Minimal parser for simple key/value YAML layout used in task_routing.yml.
    routes = {}
    current = None
    with path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            if not line.startswith(" "):
                current = line.split(":")[0]
                continue
            if current == "routes":
                key, value = [token.strip() for token in line.split(":", 1)]
                routes[key] = value
    return routes


def _parse_trace_line(raw_line: str) -> dict[str, Any] | None:
    line = raw_line.strip()
    if not line:
        return None
    try:
        parsed = json.loads(line)
    except json.JSONDecodeError:
        return {"raw": line}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


def read_trace_sources() -> dict[str, Any]:
    sources_raw = os.getenv("TRACE_SOURCES", "").strip()
    if not sources_raw:
        return {"status": "TRACE_SOURCE_UNAVAILABLE", "records": [], "errors": []}

    source_paths = [Path(item.strip()) for item in sources_raw.split(",") if item.strip()]
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for source_path in source_paths:
        try:
            content = source_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            errors.append({"path": str(source_path), "status": "TRACE_SOURCE_UNAVAILABLE"})
            continue
        except PermissionError:
            errors.append({"path": str(source_path), "status": "INSUFFICIENT_PRIVILEGES"})
            continue
        except OSError as exc:
            status = "TRACE_PERSISTENCE_FAILED" if getattr(exc, "errno", None) == 28 else "TRACE_READ_ERROR"
            errors.append({"path": str(source_path), "status": status, "detail": str(exc)})
            continue

        for line in content.splitlines():
            parsed = _parse_trace_line(line)
            if parsed is None:
                continue
            parsed["_trace_source"] = str(source_path)
            records.append(parsed)

    if not records:
        if errors:
            return {"status": errors[0]["status"], "records": [], "errors": errors}
        return {"status": "TRACE_SOURCE_UNAVAILABLE", "records": [], "errors": []}

    return {"status": "TRACE_RECORDS_COLLECTED", "records": records, "errors": errors}


def _metric_from_record(record: dict[str, Any], key: str) -> Any:
    if key in record:
        return record.get(key)
    metrics = record.get("metrics")
    if isinstance(metrics, dict) and key in metrics:
        return metrics.get(key)
    return None


def evaluate_trace_frames(records: list[dict[str, Any]]) -> dict[str, Any]:
    required = ["T", "W", "F", "G", "Th", "alpha", "beta"]
    frame_results: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        frame_id = record.get("frame_id", index)
        frame = {"frame_id": frame_id, "source": record.get("_trace_source")}
        values = {key: _metric_from_record(record, key) for key in required}
        frame["metrics"] = values

        missing = [key for key, value in values.items() if value is None]
        if missing:
            frame["status"] = "MISSING_DATA"
            frame["missing_fields"] = missing
            frame_results.append(frame)
            continue

        try:
            t = float(values["T"])
            w = float(values["W"])
            f = float(values["F"])
            g_t = float(values["G"])
            th = float(values["Th"])
            alpha = float(values["alpha"])
            beta = float(values["beta"])
        except (TypeError, ValueError):
            frame["status"] = "INCONSISTENT_TRACE"
            frame["detail"] = "Non-numeric metric value detected"
            frame_results.append(frame)
            continue

        frame["D"] = t * (w + f) - alpha * g_t - beta * th
        denominator = 1.0 + g_t + th
        if denominator <= 0:
            frame["status"] = "INCONSISTENT_TRACE"
            frame["detail"] = "Invalid Trust denominator"
            frame_results.append(frame)
            continue

        frame["Trust"] = t * (w + f) / denominator

        if bool(record.get("frame_dependency")):
            frame["status"] = "FRAME_DEPENDENCE_DETECTED"
        else:
            frame["status"] = "TRACE_EVALUATED"
        frame_results.append(frame)

    statuses = {item["status"] for item in frame_results}
    if not frame_results:
        overall_status = "UNABLE_TO_PERFORM_REAL_TRACE_EVALUATION"
    elif "FRAME_DEPENDENCE_DETECTED" in statuses:
        overall_status = "FRAME_DEPENDENCE_DETECTED"
    elif "INCONSISTENT_TRACE" in statuses:
        overall_status = "INCONSISTENT_TRACE"
    elif "MISSING_DATA" in statuses:
        overall_status = "MISSING_DATA"
    elif statuses == {"TRACE_EVALUATED"}:
        overall_status = "TRACE_EVALUATION_COMPLETE"
    else:
        overall_status = "UNABLE_TO_PERFORM_REAL_TRACE_EVALUATION"

    return {"status": overall_status, "frames": frame_results}


def get_account_context() -> dict:
    account_context = os.getenv("ACCOUNT_CONTEXT", "gmail").strip().lower()
    if account_context not in ACCOUNT_MATRIX:
        raise ValueError(
            f"Unsupported ACCOUNT_CONTEXT={account_context}. "
            f"Allowed: {', '.join(ACCOUNT_MATRIX)}"
        )

    profile = ACCOUNT_MATRIX[account_context]
    token = os.getenv(profile["token_env"], "")
    return {
        "context": account_context,
        "email": profile["email"],
        "token_env": profile["token_env"],
        "has_token": bool(token),
    }


def build_connector_actions(capability_map: dict) -> list[dict]:
    actions = []
    for connector, state in capability_map.items():
        if state in {"blocked", "unstable", "retry_required", "noisy"}:
            action = "skip_or_retry"
        else:
            action = "execute"
        actions.append({"connector": connector, "state": state, "action": action})
    return actions


def build_task_assignments(routes: dict) -> list[dict]:
    return [{"task_type": task_type, "assign_to": connector} for task_type, connector in routes.items()]


def main() -> int:
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        account = get_account_context()
    except ValueError as exc:
        print(f"❌ {exc}")
        return 2

    validation = validate_dr_protocol()
    capability_map = load_json(CAPABILITY_MAP_PATH)
    routes = load_task_routes(TASK_ROUTING_PATH)
    trace_source_result = read_trace_sources()
    trace_result = {
        "status": trace_source_result["status"],
        "source_errors": trace_source_result["errors"],
        "frame_evaluation": {"status": "UNABLE_TO_PERFORM_REAL_TRACE_EVALUATION", "frames": []},
    }
    if trace_source_result["status"] == "TRACE_RECORDS_COLLECTED":
        trace_result["frame_evaluation"] = evaluate_trace_frames(trace_source_result["records"])
        trace_result["status"] = trace_result["frame_evaluation"]["status"]

    result = {
        "timestamp": timestamp,
        "account_context": account,
        "validation": validation,
        "trace_evaluation": trace_result,
        "connector_actions": build_connector_actions(capability_map),
        "task_assignments": build_task_assignments(routes),
        "policy_gate": {
            "ci_pass": validation["passed"],
            "dr_protocol_valid": validation["passed"],
            "real_trace_ok": trace_result["status"] == "TRACE_EVALUATION_COMPLETE",
            "no_exception": validation["passed"]
            and trace_result["status"] == "TRACE_EVALUATION_COMPLETE",
            "decision": (
                "enable_auto_merge"
                if validation["passed"] and trace_result["status"] == "TRACE_EVALUATION_COMPLETE"
                else "review_required"
            ),
        },
    }

    print(json.dumps(result, indent=2))

    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"policy_decision={result['policy_gate']['decision']}\n")
            fh.write(f"validation_passed={str(validation['passed']).lower()}\n")
            fh.write(f"trace_status={trace_result['status']}\n")

    return 0 if result["policy_gate"]["decision"] == "enable_auto_merge" else 1


if __name__ == "__main__":
    sys.exit(main())
