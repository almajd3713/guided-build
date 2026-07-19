#!/usr/bin/env python3
"""Contract, evidence, and private-state support for Guided Build."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

CONTRACT_SCHEMA = "guided-build/v1"
EVIDENCE_SCHEMA = "guided-build/evidence/v1"
STATE_SCHEMA_VERSION = 1
DEPTHS = {"fast", "balanced", "deep"}
DELIVERY_STATUSES = {"not_started", "in_progress", "blocked", "complete"}
MASTERY_STATUSES = {"unassessed", "introduced", "practiced", "demonstrated", "revisit_due"}
PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
MILESTONE_RE = re.compile(r"^###\s+([A-Z][A-Z0-9_-]*\d+)\s+[—-]\s+(.+?)\s*$")
SUBHEADING_RE = re.compile(r"^####\s+(.+?)\s*$")

REQUIRED_CONTRACT_SECTIONS = {"outcomes", "non-goals", "validation", "milestones"}
REQUIRED_MILESTONE_SECTIONS = {
    "objective",
    "prerequisites",
    "concepts",
    "delivery scope",
    "exclusions",
    "validation",
    "learning evidence",
    "dependent milestones",
}
REQUIRED_EVIDENCE_SECTIONS = {
    "scope and ownership",
    "changes",
    "validation results",
    "learning evidence",
    "deviations and debt",
    "acceptance",
}


class GuidedBuildError(Exception):
    """An actionable validation or state-management error."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise GuidedBuildError(f"cannot read {path}: {exc}") from exc
    if not lines or lines[0].strip() != "---":
        raise GuidedBuildError(f"{path} must begin with frontmatter delimited by ---")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise GuidedBuildError(f"{path} has unterminated frontmatter") from exc

    metadata: dict[str, Any] = {}
    for line_number, raw in enumerate(lines[1:end], 2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            raise GuidedBuildError(f"{path}:{line_number}: expected key: value")
        key, value = (part.strip() for part in raw.split(":", 1))
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            raise GuidedBuildError(f"{path}:{line_number}: invalid key {key!r}")
        if key in metadata:
            raise GuidedBuildError(f"{path}:{line_number}: duplicate key {key!r}")
        if not value:
            raise GuidedBuildError(f"{path}:{line_number}: empty values are unsupported")
        try:
            metadata[key] = json.loads(value)
        except json.JSONDecodeError:
            metadata[key] = value
    return metadata, lines[end + 1 :]


def headings(lines: Iterable[str], level: int) -> set[str]:
    prefix = "#" * level + " "
    return {normalized(line[len(prefix) :]) for line in lines if line.startswith(prefix)}


def section_body(lines: list[str], section_name: str) -> list[str] | None:
    target = f"## {section_name}"
    section_start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith("## ") and normalized(line) == normalized(target)
        ),
        None,
    )
    if section_start is None:
        return None
    content = []
    for line in lines[section_start + 1 :]:
        if line.startswith("## "):
            break
        content.append(line)
    return content


def referenced_ids(lines: Iterable[str]) -> list[str]:
    result = []
    for line in lines:
        match = re.match(r"^\s*-\s+([A-Z][A-Z0-9_-]*\d+)\b", line)
        if match:
            result.append(match.group(1))
    return result


def bullet_values(lines: Iterable[str]) -> list[str]:
    values = []
    for line in lines:
        match = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if match and match.group(1).lower() != "none":
            values.append(match.group(1))
    return values


def parse_milestones(lines: list[str]) -> dict[str, dict[str, Any]]:
    milestones: dict[str, dict[str, Any]] = {}
    current_id: str | None = None
    current_section: str | None = None
    for body_line, line in enumerate(lines, 1):
        match = MILESTONE_RE.match(line)
        if match:
            current_id = match.group(1)
            if current_id in milestones:
                raise GuidedBuildError(f"duplicate milestone {current_id} near body line {body_line}")
            milestones[current_id] = {"title": match.group(2), "sections": {}}
            current_section = None
            continue
        subsection = SUBHEADING_RE.match(line)
        if subsection and current_id:
            current_section = normalized(subsection.group(1))
            milestones[current_id]["sections"].setdefault(current_section, [])
            continue
        if current_id and current_section:
            milestones[current_id]["sections"][current_section].append(line)

    for milestone in milestones.values():
        milestone["prerequisites"] = referenced_ids(
            milestone["sections"].get("prerequisites", [])
        )
        milestone["dependents"] = referenced_ids(
            milestone["sections"].get("dependent milestones", [])
        )
        milestone["concepts"] = bullet_values(
            milestone["sections"].get("concepts", [])
        )
    return milestones


def ensure_acyclic(milestones: dict[str, dict[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(milestone_id: str) -> None:
        if milestone_id in visiting:
            raise GuidedBuildError(f"dependency cycle includes {milestone_id}")
        if milestone_id in visited:
            return
        visiting.add(milestone_id)
        for prerequisite in milestones[milestone_id]["prerequisites"]:
            visit(prerequisite)
        visiting.remove(milestone_id)
        visited.add(milestone_id)

    for milestone_id in milestones:
        visit(milestone_id)


def validate_contract(path: Path) -> dict[str, Any]:
    metadata, lines = parse_frontmatter(path)
    errors: list[str] = []
    warnings: list[str] = []
    required = {"schema", "project_id", "title", "plan_sources", "default_depth", "status"}
    missing = sorted(required - metadata.keys())
    if missing:
        errors.append("missing frontmatter keys: " + ", ".join(missing))
    if metadata.get("schema") != CONTRACT_SCHEMA:
        errors.append(f"schema must be {CONTRACT_SCHEMA!r}")
    project_id = metadata.get("project_id")
    if not isinstance(project_id, str) or not PROJECT_ID_RE.fullmatch(project_id):
        errors.append("project_id must be 2-64 lowercase letters, digits, underscores, or hyphens")
    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string")
    if metadata.get("default_depth") not in DEPTHS:
        errors.append("default_depth must be fast, balanced, or deep")
    if metadata.get("status") not in {"draft", "approved"}:
        errors.append("status must be draft or approved")
    sources = metadata.get("plan_sources")
    if not isinstance(sources, list) or not sources or not all(
        isinstance(source, str) and source.strip() for source in sources
    ):
        errors.append("plan_sources must be a non-empty JSON-style array of strings")
    absent_sections = sorted(REQUIRED_CONTRACT_SECTIONS - headings(lines, 2))
    if absent_sections:
        errors.append("missing contract sections: " + ", ".join(absent_sections))
    for section_name in REQUIRED_CONTRACT_SECTIONS - set(absent_sections):
        content = section_body(lines, section_name)
        if content is not None and not any(line.strip() for line in content):
            errors.append(f"contract section {section_name!r} is empty")

    try:
        milestones = parse_milestones(lines)
    except GuidedBuildError as exc:
        errors.append(str(exc))
        milestones = {}
    if not milestones:
        errors.append("define at least one heading like: ### M01 — Milestone title")
    for milestone_id, milestone in milestones.items():
        sections = milestone["sections"]
        absent = sorted(REQUIRED_MILESTONE_SECTIONS - sections.keys())
        if absent:
            errors.append(f"{milestone_id} missing subsections: {', '.join(absent)}")
        for section_name in REQUIRED_MILESTONE_SECTIONS & sections.keys():
            if not any(line.strip() for line in sections[section_name]):
                errors.append(f"{milestone_id} subsection {section_name!r} is empty")
        for reference in milestone["prerequisites"] + milestone["dependents"]:
            if reference not in milestones:
                errors.append(f"{milestone_id} references unknown milestone {reference}")
    if milestones and not errors:
        try:
            ensure_acyclic(milestones)
        except GuidedBuildError as exc:
            errors.append(str(exc))
    for milestone_id, milestone in milestones.items():
        for dependent in milestone["dependents"]:
            if dependent in milestones and milestone_id not in milestones[dependent]["prerequisites"]:
                warnings.append(
                    f"{milestone_id} lists {dependent} as dependent, but the reverse prerequisite is absent"
                )

    public_milestones = {
        milestone_id: {
            "title": item["title"],
            "prerequisites": item["prerequisites"],
            "dependents": item["dependents"],
            "concepts": item["concepts"],
        }
        for milestone_id, item in milestones.items()
    }
    return {
        "valid": not errors,
        "path": str(path),
        "metadata": metadata,
        "milestones": public_milestones,
        "errors": errors,
        "warnings": warnings,
    }


def validate_evidence(path: Path, contract_path: Path | None) -> dict[str, Any]:
    metadata, lines = parse_frontmatter(path)
    errors = []
    if metadata.get("schema") != EVIDENCE_SCHEMA:
        errors.append(f"schema must be {EVIDENCE_SCHEMA!r}")
    for key in ("milestone_id", "depth", "delivery_status"):
        if key not in metadata:
            errors.append(f"missing frontmatter key {key}")
    if metadata.get("depth") not in DEPTHS:
        errors.append("depth must be fast, balanced, or deep")
    if metadata.get("delivery_status") not in DELIVERY_STATUSES:
        errors.append("delivery_status is invalid")
    absent = sorted(REQUIRED_EVIDENCE_SECTIONS - headings(lines, 2))
    if absent:
        errors.append("missing evidence sections: " + ", ".join(absent))
    for section_name in REQUIRED_EVIDENCE_SECTIONS - set(absent):
        content = section_body(lines, section_name)
        if content is not None and not any(line.strip() for line in content):
            errors.append(f"evidence section {section_name!r} is empty")
    if contract_path:
        contract = validate_contract(contract_path)
        if not contract["valid"]:
            errors.append("referenced contract is invalid")
        elif metadata.get("milestone_id") not in contract["milestones"]:
            errors.append(f"unknown milestone_id {metadata.get('milestone_id')!r}")
    return {"valid": not errors, "path": str(path), "metadata": metadata, "errors": errors}


def git_value(repo: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *arguments],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def private_state_root() -> Path:
    override = os.environ.get("GUIDED_BUILD_STATE_HOME")
    if override:
        return Path(override)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Guided Build"
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Guided Build"
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "guided-build"


def state_location(contract_path: Path, repo: Path) -> tuple[Path, dict[str, Any]]:
    contract = validate_contract(contract_path)
    if not contract["valid"]:
        raise GuidedBuildError("contract is invalid: " + "; ".join(contract["errors"]))
    project_id = contract["metadata"]["project_id"]
    identity = git_value(repo, "remote", "get-url", "origin") or str(repo.resolve())
    fingerprint = hashlib.sha256(f"{project_id}\0{identity}".encode()).hexdigest()[:20]
    return private_state_root() / project_id / f"{fingerprint}.json", contract


def new_state(contract_path: Path, repo: Path, contract: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "project_id": contract["metadata"]["project_id"],
        "contract_path": str(contract_path.resolve()),
        "repo_hint": str(repo.resolve()),
        "active_milestone": None,
        "milestones": {
            milestone_id: {
                "delivery_status": "not_started",
                "depth": None,
                "active_slice": None,
                "concepts": list(contract["milestones"][milestone_id]["concepts"]),
            }
            for milestone_id in contract["milestones"]
        },
        "concepts": {},
        "session_notes": [],
        "created_at": now,
        "updated_at": now,
    }


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_state(
    contract_path: Path, repo: Path, *, create: bool = False
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    location, contract = state_location(contract_path, repo)
    if not location.exists():
        if not create:
            raise GuidedBuildError("private state does not exist; run init-state")
        state = new_state(contract_path, repo, contract)
        atomic_json(location, state)
        return location, state, contract
    try:
        state = json.loads(location.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GuidedBuildError(f"cannot read private state {location}: {exc}") from exc
    validate_state_structure(state, contract)
    for milestone_id in contract["milestones"]:
        state.setdefault("milestones", {}).setdefault(
            milestone_id,
            {
                "delivery_status": "not_started",
                "depth": None,
                "active_slice": None,
                "concepts": [],
            },
        )
    return location, state, contract


def validate_state_structure(state: Any, contract: dict[str, Any]) -> None:
    if not isinstance(state, dict):
        raise GuidedBuildError("private state must be a JSON object")
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        raise GuidedBuildError(f"unsupported private state schema {state.get('schema_version')!r}")
    if state.get("project_id") != contract["metadata"]["project_id"]:
        raise GuidedBuildError("private state belongs to another project")
    if not isinstance(state.get("milestones"), dict):
        raise GuidedBuildError("private state milestones must be an object")
    if not isinstance(state.get("concepts"), dict):
        raise GuidedBuildError("private state concepts must be an object")
    if not isinstance(state.get("session_notes"), list):
        raise GuidedBuildError("private state session_notes must be an array")


def validate_contract_command(args: argparse.Namespace) -> int:
    report = validate_contract(args.contract)
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


def validate_evidence_command(args: argparse.Namespace) -> int:
    report = validate_evidence(args.evidence, args.contract)
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


def init_state_command(args: argparse.Namespace) -> int:
    location, state, _ = load_state(args.contract, args.repo, create=True)
    print(json.dumps({"state_path": str(location), "state": state}, indent=2))
    return 0


def status_command(args: argparse.Namespace) -> int:
    location, state, _ = load_state(args.contract, args.repo)
    visible = json.loads(json.dumps(state))
    if not args.include_private_notes:
        visible["session_notes"] = []
        for concept in visible.get("concepts", {}).values():
            concept.pop("confidence", None)
            concept.pop("misconceptions", None)
    print(json.dumps({"state_path": str(location), "state": visible}, indent=2))
    return 0


def start_milestone_command(args: argparse.Namespace) -> int:
    location, state, contract = load_state(args.contract, args.repo, create=True)
    if contract["metadata"]["status"] != "approved":
        raise GuidedBuildError("contract must be approved before milestone work")
    if args.milestone not in contract["milestones"]:
        raise GuidedBuildError(f"unknown milestone {args.milestone}")
    unresolved = []
    for prerequisite in contract["milestones"][args.milestone]["prerequisites"]:
        prior = state["milestones"].get(prerequisite, {})
        if prior.get("delivery_status") != "complete":
            unresolved.append(f"{prerequisite} delivery is incomplete")
        for concept_name in prior.get("concepts", []):
            mastery = state["concepts"].get(concept_name, {}).get(
                "mastery_status", "unassessed"
            )
            if mastery in {"unassessed", "introduced", "practiced", "revisit_due"}:
                unresolved.append(f"concept {concept_name!r} requires review")
    if unresolved:
        raise GuidedBuildError("prerequisite gate failed: " + "; ".join(unresolved))
    state["active_milestone"] = args.milestone
    item = state["milestones"][args.milestone]
    item.update(
        delivery_status="in_progress", depth=args.depth, active_slice=args.slice
    )
    state["updated_at"] = utc_now()
    atomic_json(location, state)
    print(json.dumps({"active_milestone": args.milestone, "depth": args.depth}, indent=2))
    return 0


def set_delivery_command(args: argparse.Namespace) -> int:
    location, state, contract = load_state(args.contract, args.repo)
    if args.milestone not in contract["milestones"]:
        raise GuidedBuildError(f"unknown milestone {args.milestone}")
    if args.status == "complete":
        if args.evidence is None:
            raise GuidedBuildError("delivery completion requires --evidence")
        report = validate_evidence(args.evidence, args.contract)
        if not report["valid"]:
            raise GuidedBuildError("evidence is invalid: " + "; ".join(report["errors"]))
        if report["metadata"].get("milestone_id") != args.milestone:
            raise GuidedBuildError("evidence belongs to another milestone")
        if report["metadata"].get("delivery_status") != "complete":
            raise GuidedBuildError("evidence delivery_status must be complete")
    item = state["milestones"][args.milestone]
    item["delivery_status"] = args.status
    if args.slice is not None:
        item["active_slice"] = args.slice or None
    if args.status == "complete" and state.get("active_milestone") == args.milestone:
        state["active_milestone"] = None
        item["active_slice"] = None
    state["updated_at"] = utc_now()
    atomic_json(location, state)
    print(json.dumps({"milestone": args.milestone, "delivery_status": args.status}, indent=2))
    return 0


def record_concept_command(args: argparse.Namespace) -> int:
    location, state, contract = load_state(args.contract, args.repo)
    if args.milestone not in contract["milestones"]:
        raise GuidedBuildError(f"unknown milestone {args.milestone}")
    declared = contract["milestones"][args.milestone]["concepts"]
    if args.concept not in declared:
        raise GuidedBuildError(
            f"concept {args.concept!r} is not declared by milestone {args.milestone}"
        )
    if args.mastery == "demonstrated" and not args.evidence:
        raise GuidedBuildError("demonstrated mastery requires at least one --evidence reference")
    concept = state.setdefault("concepts", {}).setdefault(args.concept, {})
    concept.update(
        mastery_status=args.mastery,
        last_milestone=args.milestone,
        updated_at=utc_now(),
    )
    if args.confidence is not None:
        concept["confidence"] = args.confidence
    if args.evidence:
        evidence = concept.setdefault("evidence_refs", [])
        evidence.extend(item for item in args.evidence if item not in evidence)
    if args.misconception:
        concept.setdefault("misconceptions", []).append(
            {"note": args.misconception, "recorded_at": utc_now(), "resolved": False}
        )
    if args.revisit_after:
        if args.revisit_after not in contract["milestones"]:
            raise GuidedBuildError(f"unknown revisit milestone {args.revisit_after}")
        concept["revisit_after_milestone"] = args.revisit_after
    milestone_concepts = state["milestones"][args.milestone].setdefault("concepts", [])
    if args.concept not in milestone_concepts:
        milestone_concepts.append(args.concept)
    state["updated_at"] = utc_now()
    atomic_json(location, state)
    print(json.dumps({"concept": args.concept, "mastery_status": args.mastery}, indent=2))
    return 0


def export_state_command(args: argparse.Namespace) -> int:
    _, state, _ = load_state(args.contract, args.repo)
    exported = json.loads(json.dumps(state))
    if not args.include_private_notes:
        for concept in exported.get("concepts", {}).values():
            concept.pop("misconceptions", None)
            concept.pop("confidence", None)
        exported["session_notes"] = []
    atomic_json(args.output, exported)
    print(
        json.dumps(
            {
                "exported_to": str(args.output),
                "private_notes_included": args.include_private_notes,
            },
            indent=2,
        )
    )
    return 0


def import_state_command(args: argparse.Namespace) -> int:
    location, contract = state_location(args.contract, args.repo)
    if location.exists() and not args.replace:
        raise GuidedBuildError("private state exists; pass --replace to import intentionally")
    try:
        imported = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GuidedBuildError(f"cannot import {args.input}: {exc}") from exc
    if imported.get("schema_version") != STATE_SCHEMA_VERSION:
        raise GuidedBuildError("imported state has an unsupported schema")
    if imported.get("project_id") != contract["metadata"]["project_id"]:
        raise GuidedBuildError("imported state belongs to another project")
    validate_state_structure(imported, contract)
    if location.exists():
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(location, location.with_suffix(f".json.{stamp}.bak"))
    imported["contract_path"] = str(args.contract.resolve())
    imported["repo_hint"] = str(args.repo.resolve())
    imported["updated_at"] = utc_now()
    atomic_json(location, imported)
    print(json.dumps({"imported_to": str(location)}, indent=2))
    return 0


def add_project_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--contract", type=Path, default=Path(".guided-build/project.md"))
    parser.add_argument("--repo", type=Path, default=Path("."))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-contract")
    validate.add_argument("contract", type=Path, nargs="?", default=Path(".guided-build/project.md"))
    validate.set_defaults(handler=validate_contract_command)

    evidence = commands.add_parser("validate-evidence")
    evidence.add_argument("evidence", type=Path)
    evidence.add_argument("--contract", type=Path)
    evidence.set_defaults(handler=validate_evidence_command)

    init_state = commands.add_parser("init-state")
    add_project_arguments(init_state)
    init_state.set_defaults(handler=init_state_command)

    status = commands.add_parser("status")
    add_project_arguments(status)
    status.add_argument("--include-private-notes", action="store_true")
    status.set_defaults(handler=status_command)

    start = commands.add_parser("start-milestone")
    add_project_arguments(start)
    start.add_argument("milestone")
    start.add_argument("--depth", choices=sorted(DEPTHS), required=True)
    start.add_argument("--slice")
    start.set_defaults(handler=start_milestone_command)

    delivery = commands.add_parser("set-delivery")
    add_project_arguments(delivery)
    delivery.add_argument("milestone")
    delivery.add_argument("status", choices=sorted(DELIVERY_STATUSES))
    delivery.add_argument("--slice")
    delivery.add_argument("--evidence", type=Path)
    delivery.set_defaults(handler=set_delivery_command)

    concept = commands.add_parser("record-concept")
    add_project_arguments(concept)
    concept.add_argument("milestone")
    concept.add_argument("concept")
    concept.add_argument("mastery", choices=sorted(MASTERY_STATUSES))
    concept.add_argument("--evidence", action="append")
    concept.add_argument("--confidence", type=int, choices=range(1, 6))
    concept.add_argument("--misconception")
    concept.add_argument("--revisit-after")
    concept.set_defaults(handler=record_concept_command)

    export = commands.add_parser("export-state")
    add_project_arguments(export)
    export.add_argument("output", type=Path)
    export.add_argument("--include-private-notes", action="store_true")
    export.set_defaults(handler=export_state_command)

    import_state = commands.add_parser("import-state")
    add_project_arguments(import_state)
    import_state.add_argument("input", type=Path)
    import_state.add_argument("--replace", action="store_true")
    import_state.set_defaults(handler=import_state_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except GuidedBuildError as exc:
        print(f"guided-build: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
