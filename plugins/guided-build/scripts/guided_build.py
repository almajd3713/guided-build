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

CONTRACT_SCHEMA = "guided-build/v2"
EVIDENCE_SCHEMA = "guided-build/evidence/v2"
STATE_SCHEMA_VERSION = 2
DEPTHS = {"fast", "balanced", "deep"}
GRANULARITY_STYLES = {"adaptive", "lean", "thorough"}
DELIVERY_STATUSES = {"not_started", "in_progress", "blocked", "complete"}
MASTERY_STATUSES = {"unassessed", "introduced", "practiced", "demonstrated", "revisit_due"}
FAMILIARITY_LEVELS = {"new", "some_exposure", "comfortable"}
GUIDANCE_STYLES = {"adaptive", "theory_first", "example_first", "execution_first"}
VERBOSITY_STYLES = {"compact", "adaptive", "detailed"}
STRUGGLE_POLICIES = {"offer_choices", "auto_scaffold", "keep_coaching"}
PRIVATE_CONCEPT_FIELDS = {"confidence", "familiarity", "misconceptions"}
PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
MILESTONE_RE = re.compile(r"^###\s+([A-Z][A-Z0-9_-]*\d+)\s+[—-]\s+(.+?)\s*$")
SUBHEADING_RE = re.compile(r"^####\s+(.+?)\s*$")
CAPABILITY_HEADING_RE = re.compile(
    r"^#####\s+([A-Z][A-Z0-9_-]*\d+\.C\d+)\s+[—-]\s+(.+?)\s*$"
)
COMPOSITE_CONCEPT_RE = re.compile(r";|,.*\b(?:and|or)\b", re.IGNORECASE)
PRIVATE_EVIDENCE_PATTERNS = {
    "learner self-report": re.compile(r"\b(?:learner\s+)?self[- ]report(?:ed|s|ing)?\b", re.IGNORECASE),
    "confidence rating": re.compile(r"\bconfidence\s+(?:rating|score|level)\b", re.IGNORECASE),
    "misconception note": re.compile(r"\bmisconception(?:s|\s+note)?\b", re.IGNORECASE),
    "guidance preference": re.compile(r"\b(?:guidance|learning)\s+preference(?:s)?\b", re.IGNORECASE),
    "private-state label": re.compile(r"\bprivate[- ]state\b", re.IGNORECASE),
}

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
    "capability bundles",
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
    current_capability: str | None = None
    for body_line, line in enumerate(lines, 1):
        match = MILESTONE_RE.match(line)
        if match:
            current_id = match.group(1)
            if current_id in milestones:
                raise GuidedBuildError(f"duplicate milestone {current_id} near body line {body_line}")
            milestones[current_id] = {"title": match.group(2), "sections": {}, "capabilities": {}}
            current_section = None
            current_capability = None
            continue
        capability = CAPABILITY_HEADING_RE.match(line)
        if capability and current_id:
            capability_id = capability.group(1)
            if not capability_id.startswith(f"{current_id}.C"):
                raise GuidedBuildError(
                    f"capability {capability_id} does not belong to milestone {current_id}"
                )
            if capability_id in milestones[current_id]["capabilities"]:
                raise GuidedBuildError(f"duplicate capability {capability_id} near body line {body_line}")
            current_section = "capability bundles"
            current_capability = capability_id
            milestones[current_id]["capabilities"][capability_id] = {
                "title": capability.group(2),
                "fields": {},
            }
            continue
        subsection = SUBHEADING_RE.match(line)
        if subsection and current_id:
            current_section = normalized(subsection.group(1))
            milestones[current_id]["sections"].setdefault(current_section, [])
            current_capability = None
            continue
        if current_id and current_capability:
            field = re.match(r"^\s*-\s+(Outcome|Concepts|Prerequisites|Deliverables|Validation):\s+(.+?)\s*$", line)
            if field:
                key = normalized(field.group(1))
                raw_value = field.group(2)
                try:
                    value = json.loads(raw_value)
                except json.JSONDecodeError:
                    value = raw_value
                milestones[current_id]["capabilities"][current_capability]["fields"][key] = value
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


def ensure_capabilities_acyclic(milestone_id: str, capabilities: dict[str, dict[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(capability_id: str) -> None:
        if capability_id in visiting:
            raise GuidedBuildError(f"capability dependency cycle includes {capability_id}")
        if capability_id in visited:
            return
        visiting.add(capability_id)
        for prerequisite in capabilities[capability_id]["fields"].get("prerequisites", []):
            if prerequisite in capabilities:
                visit(prerequisite)
        visiting.remove(capability_id)
        visited.add(capability_id)

    for capability_id in capabilities:
        visit(capability_id)


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
    required = {
        "schema",
        "project_id",
        "title",
        "plan_sources",
        "default_depth",
        "default_granularity",
        "status",
    }
    missing = sorted(required - metadata.keys())
    if missing:
        errors.append("missing frontmatter keys: " + ", ".join(missing))
    if metadata.get("schema") != CONTRACT_SCHEMA:
        if metadata.get("schema") == "guided-build/v1":
            errors.append(
                "guided-build/v1 is no longer supported; migrate or regenerate the contract with Guided Build onboarding"
            )
        else:
            errors.append(f"schema must be {CONTRACT_SCHEMA!r}")
    project_id = metadata.get("project_id")
    if not isinstance(project_id, str) or not PROJECT_ID_RE.fullmatch(project_id):
        errors.append("project_id must be 2-64 lowercase letters, digits, underscores, or hyphens")
    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string")
    if metadata.get("default_depth") not in DEPTHS:
        errors.append("default_depth must be fast, balanced, or deep")
    if metadata.get("default_granularity") not in GRANULARITY_STYLES:
        errors.append("default_granularity must be adaptive, lean, or thorough")
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
            if section_name == "capability bundles" and milestone["capabilities"]:
                continue
            if not any(line.strip() for line in sections[section_name]):
                errors.append(f"{milestone_id} subsection {section_name!r} is empty")
        for reference in milestone["prerequisites"] + milestone["dependents"]:
            if reference not in milestones:
                errors.append(f"{milestone_id} references unknown milestone {reference}")
        capabilities = milestone["capabilities"]
        if not capabilities:
            errors.append(f"{milestone_id} must define at least one capability bundle")
        if len(capabilities) > 8:
            warnings.append(
                f"{milestone_id} defines {len(capabilities)} capabilities; prefer at most 8"
            )
        expected_fields = {"outcome", "concepts", "prerequisites", "deliverables", "validation"}
        for capability_id, capability in capabilities.items():
            fields = capability["fields"]
            missing_fields = sorted(expected_fields - fields.keys())
            if missing_fields:
                errors.append(
                    f"{capability_id} missing fields: {', '.join(missing_fields)}"
                )
                continue
            if not isinstance(fields["outcome"], str) or not fields["outcome"].strip():
                errors.append(f"{capability_id} Outcome must be a non-empty string")
            if not isinstance(fields["validation"], str) or not fields["validation"].strip():
                errors.append(f"{capability_id} Validation must be a non-empty string")
            for key in ("concepts", "prerequisites", "deliverables"):
                value = fields[key]
                if not isinstance(value, list) or not all(
                    isinstance(item, str) and item.strip() for item in value
                ):
                    errors.append(f"{capability_id} {key.title()} must be a JSON array of strings")
            if isinstance(fields["deliverables"], list) and not fields["deliverables"]:
                errors.append(f"{capability_id} Deliverables must not be empty")
            if isinstance(fields["concepts"], list):
                for concept in fields["concepts"]:
                    if concept not in milestone["concepts"]:
                        errors.append(
                            f"{capability_id} references undeclared concept {concept!r}"
                        )
            if isinstance(fields["prerequisites"], list):
                for prerequisite in fields["prerequisites"]:
                    if prerequisite not in capabilities:
                        errors.append(
                            f"{capability_id} references unknown capability {prerequisite}"
                        )
        try:
            ensure_capabilities_acyclic(milestone_id, capabilities)
        except GuidedBuildError as exc:
            errors.append(str(exc))
    if milestones and not errors:
        try:
            ensure_acyclic(milestones)
        except GuidedBuildError as exc:
            errors.append(str(exc))
    for milestone_id, milestone in milestones.items():
        for concept in milestone["concepts"]:
            if COMPOSITE_CONCEPT_RE.search(concept):
                warnings.append(
                    f"{milestone_id} concept {concept!r} may be composite; prefer one atomic concept per bullet"
                )
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
            "capabilities": {
                capability_id: {
                    "title": capability["title"],
                    **capability["fields"],
                }
                for capability_id, capability in item["capabilities"].items()
            },
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
    errors: list[str] = []
    warnings: list[str] = []
    if metadata.get("schema") != EVIDENCE_SCHEMA:
        errors.append(f"schema must be {EVIDENCE_SCHEMA!r}")
    for key in (
        "milestone_id",
        "depth",
        "granularity",
        "delivery_status",
        "active_capability",
        "completed_capabilities",
    ):
        if key not in metadata:
            errors.append(f"missing frontmatter key {key}")
    if metadata.get("depth") not in DEPTHS:
        errors.append("depth must be fast, balanced, or deep")
    if metadata.get("granularity") not in GRANULARITY_STYLES:
        errors.append("granularity must be adaptive, lean, or thorough")
    if metadata.get("delivery_status") not in DELIVERY_STATUSES:
        errors.append("delivery_status is invalid")
    absent = sorted(REQUIRED_EVIDENCE_SECTIONS - headings(lines, 2))
    if absent:
        errors.append("missing evidence sections: " + ", ".join(absent))
    for section_name in REQUIRED_EVIDENCE_SECTIONS - set(absent):
        content = section_body(lines, section_name)
        if content is not None and not any(line.strip() for line in content):
            errors.append(f"evidence section {section_name!r} is empty")
    body = "\n".join(lines)
    for label, pattern in PRIVATE_EVIDENCE_PATTERNS.items():
        if pattern.search(body):
            errors.append(f"evidence contains a forbidden private learner label: {label}")
    completed = metadata.get("completed_capabilities")
    if not isinstance(completed, list) or not all(isinstance(item, str) for item in completed):
        errors.append("completed_capabilities must be a JSON array of strings")
        completed = []
    elif len(completed) != len(set(completed)):
        errors.append("completed_capabilities must not contain duplicates")
    active = metadata.get("active_capability")
    if not isinstance(active, str):
        errors.append("active_capability must be a capability ID or 'none'")
        active = "none"
    if active != "none" and active in completed:
        errors.append("active_capability must not also be completed")

    contract = None
    if contract_path:
        contract = validate_contract(contract_path)
        if not contract["valid"]:
            errors.append("referenced contract is invalid")
        elif metadata.get("milestone_id") not in contract["milestones"]:
            errors.append(f"unknown milestone_id {metadata.get('milestone_id')!r}")
        else:
            milestone = contract["milestones"][metadata["milestone_id"]]
            capability_ids = set(milestone["capabilities"])
            for capability_id in completed:
                if capability_id not in capability_ids:
                    errors.append(f"unknown completed capability {capability_id}")
            if active != "none" and active not in capability_ids:
                errors.append(f"unknown active capability {active}")
            if metadata.get("delivery_status") == "complete":
                if active != "none":
                    errors.append("complete evidence must set active_capability to 'none'")
                if set(completed) != capability_ids:
                    errors.append("complete evidence must list every milestone capability as completed")

    snapshot_lines: list[str] = []
    log_lines: list[str] = []
    in_log = False
    for line in lines:
        if line.startswith("## ") and normalized(line[3:]) == "slice log":
            in_log = True
            continue
        if in_log:
            log_lines.append(line)
        elif not line.startswith("# "):
            snapshot_lines.append(line)
    snapshot_words = len(re.findall(r"\b[\w'-]+\b", "\n".join(snapshot_lines)))
    if snapshot_words > 600:
        warnings.append(
            f"compaction_required: authoritative snapshot has {snapshot_words} words; maximum is 600"
        )
    log_entries: list[list[str]] = []
    current_entry: list[str] | None = None
    for line in log_lines:
        if re.match(r"^###\s+", line):
            if current_entry is not None:
                log_entries.append(current_entry)
            current_entry = [line]
        elif current_entry is not None:
            current_entry.append(line)
    if current_entry is not None:
        log_entries.append(current_entry)
    if len(log_entries) > 5:
        warnings.append(
            f"compaction_required: slice log has {len(log_entries)} entries; maximum is 5"
        )
    for index, entry in enumerate(log_entries, 1):
        words = len(re.findall(r"\b[\w'-]+\b", "\n".join(entry)))
        if words > 60:
            warnings.append(
                f"compaction_required: slice log entry {index} has {words} words; maximum is 60"
            )
    return {
        "valid": not errors,
        "path": str(path),
        "metadata": metadata,
        "errors": errors,
        "warnings": warnings,
        "compaction_required": any("compaction_required" in item for item in warnings),
        "metrics": {"snapshot_words": snapshot_words, "log_entries": len(log_entries)},
    }


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
                "granularity": None,
                "active_slice": None,
                "active_capability": None,
                "capabilities": {
                    capability_id: {"delivery_status": "not_started"}
                    for capability_id in contract["milestones"][milestone_id]["capabilities"]
                },
                "retired_capabilities": {},
                "concepts": list(contract["milestones"][milestone_id]["concepts"]),
            }
            for milestone_id in contract["milestones"]
        },
        "concepts": {},
        "preferences": {},
        "calibration_topics": {},
        "session_notes": [],
        "created_at": now,
        "updated_at": now,
    }


def backup_state(path: Path) -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_suffix(f".json.{stamp}.bak")
    counter = 1
    while backup.exists():
        backup = path.with_suffix(f".json.{stamp}.{counter}.bak")
        counter += 1
    shutil.copy2(path, backup)
    return backup


def migrate_state_v1(state: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    migrated = json.loads(json.dumps(state))
    migrated["schema_version"] = STATE_SCHEMA_VERSION
    for milestone_id, contract_milestone in contract["milestones"].items():
        milestone = migrated.setdefault("milestones", {}).setdefault(milestone_id, {})
        milestone.setdefault("delivery_status", "not_started")
        milestone.setdefault("depth", None)
        milestone.setdefault("granularity", None)
        milestone.setdefault("active_slice", None)
        milestone["active_capability"] = None
        milestone["capabilities"] = {
            capability_id: {"delivery_status": "not_started"}
            for capability_id in contract_milestone["capabilities"]
        }
        milestone.setdefault("retired_capabilities", {})
        milestone["concepts"] = list(contract_milestone["concepts"])
    migrated.setdefault("preferences", {})
    migrated.setdefault("calibration_topics", {})
    migrated.setdefault("session_notes", [])
    migrated["updated_at"] = utc_now()
    return migrated


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
    if isinstance(state, dict) and state.get("schema_version") == 1:
        backup_state(location)
        state = migrate_state_v1(state, contract)
        atomic_json(location, state)
    validate_state_structure(state, contract)
    state.setdefault("preferences", {})
    state.setdefault("calibration_topics", {})
    for milestone_id in contract["milestones"]:
        milestone = state.setdefault("milestones", {}).setdefault(
            milestone_id,
            {
                "delivery_status": "not_started",
                "depth": None,
                "granularity": None,
                "active_slice": None,
                "active_capability": None,
                "capabilities": {},
                "retired_capabilities": {},
                "concepts": [],
            },
        )
        milestone["concepts"] = list(contract["milestones"][milestone_id]["concepts"])
        milestone.setdefault("granularity", None)
        milestone.setdefault("active_capability", None)
        capabilities = milestone.setdefault("capabilities", {})
        retired_capabilities = milestone.setdefault("retired_capabilities", {})
        for capability_id in contract["milestones"][milestone_id]["capabilities"]:
            capabilities.setdefault(capability_id, {"delivery_status": "not_started"})
        for capability_id in list(capabilities):
            if capability_id not in contract["milestones"][milestone_id]["capabilities"]:
                retired_capabilities.setdefault(capability_id, capabilities.pop(capability_id))
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
    if "preferences" in state and not isinstance(state["preferences"], dict):
        raise GuidedBuildError("private state preferences must be an object")
    if "calibration_topics" in state and not isinstance(state["calibration_topics"], dict):
        raise GuidedBuildError("private state calibration_topics must be an object")
    for milestone_id, milestone in state["milestones"].items():
        if not isinstance(milestone, dict):
            raise GuidedBuildError(f"private state milestone {milestone_id} must be an object")
        if "capabilities" in milestone and not isinstance(milestone["capabilities"], dict):
            raise GuidedBuildError(f"private state milestone {milestone_id} capabilities must be an object")
        if "retired_capabilities" in milestone and not isinstance(
            milestone["retired_capabilities"], dict
        ):
            raise GuidedBuildError(
                f"private state milestone {milestone_id} retired_capabilities must be an object"
            )


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
    print(
        json.dumps(
            {
                "state_path": str(location),
                "project_id": state["project_id"],
                "initialized": True,
            },
            indent=2,
        )
    )
    return 0


def redact_private_notes(state: dict[str, Any]) -> dict[str, Any]:
    visible = json.loads(json.dumps(state))
    visible["session_notes"] = []
    visible.pop("preferences", None)
    visible.pop("calibration_topics", None)
    for concept in visible.get("concepts", {}).values():
        for field in PRIVATE_CONCEPT_FIELDS:
            concept.pop(field, None)
    return visible


def status_command(args: argparse.Namespace) -> int:
    location, state, _ = load_state(args.contract, args.repo)
    visible = state if args.include_private_notes else redact_private_notes(state)
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
        for concept_name in contract["milestones"][prerequisite]["concepts"]:
            mastery = state["concepts"].get(concept_name, {}).get(
                "mastery_status", "unassessed"
            )
            if mastery in {"unassessed", "introduced", "practiced", "revisit_due"}:
                unresolved.append(f"concept {concept_name!r} requires review")
    if unresolved:
        raise GuidedBuildError("prerequisite gate failed: " + "; ".join(unresolved))
    state["active_milestone"] = args.milestone
    item = state["milestones"][args.milestone]
    granularity = (
        state.get("preferences", {}).get("granularity")
        or contract["metadata"]["default_granularity"]
    )
    item.update(delivery_status="in_progress", depth=args.depth, granularity=granularity)
    state["updated_at"] = utc_now()
    atomic_json(location, state)
    print(
        json.dumps(
            {
                "active_milestone": args.milestone,
                "depth": args.depth,
                "granularity": granularity,
            },
            indent=2,
        )
    )
    return 0


def resolved_evidence_path(args: argparse.Namespace) -> Path:
    if getattr(args, "evidence", None) is not None:
        return args.evidence
    return args.repo / ".guided-build" / "evidence" / f"{args.milestone}.md"


def start_capability_command(args: argparse.Namespace) -> int:
    location, state, contract = load_state(args.contract, args.repo)
    if args.milestone not in contract["milestones"]:
        raise GuidedBuildError(f"unknown milestone {args.milestone}")
    capability_contract = contract["milestones"][args.milestone]["capabilities"]
    if args.capability not in capability_contract:
        raise GuidedBuildError(f"unknown capability {args.capability}")
    milestone = state["milestones"][args.milestone]
    if state.get("active_milestone") != args.milestone:
        raise GuidedBuildError(f"start milestone {args.milestone} before a capability")
    active = milestone.get("active_capability")
    if active and active != args.capability:
        raise GuidedBuildError(f"capability {active} is already active")
    unresolved = [
        prerequisite
        for prerequisite in capability_contract[args.capability]["prerequisites"]
        if milestone["capabilities"].get(prerequisite, {}).get("delivery_status") != "complete"
    ]
    if unresolved:
        raise GuidedBuildError(
            "capability prerequisite gate failed: " + ", ".join(unresolved)
        )
    evidence_path = resolved_evidence_path(args)
    if evidence_path.exists():
        report = validate_evidence(evidence_path, args.contract)
        if not report["valid"]:
            raise GuidedBuildError("evidence is invalid: " + "; ".join(report["errors"]))
        if report["compaction_required"]:
            raise GuidedBuildError(
                "evidence compaction is required before starting another capability"
            )
    now = utc_now()
    capability = milestone["capabilities"][args.capability]
    capability["delivery_status"] = "in_progress"
    capability.setdefault("started_at", now)
    capability.pop("completed_at", None)
    milestone["active_capability"] = args.capability
    milestone["delivery_status"] = "in_progress"
    state["updated_at"] = now
    atomic_json(location, state)
    print(json.dumps({"milestone": args.milestone, "active_capability": args.capability}, indent=2))
    return 0


def set_capability_delivery_command(args: argparse.Namespace) -> int:
    location, state, contract = load_state(args.contract, args.repo)
    if args.milestone not in contract["milestones"]:
        raise GuidedBuildError(f"unknown milestone {args.milestone}")
    if args.capability not in contract["milestones"][args.milestone]["capabilities"]:
        raise GuidedBuildError(f"unknown capability {args.capability}")
    milestone = state["milestones"][args.milestone]
    if args.status == "complete":
        evidence_path = resolved_evidence_path(args)
        if not evidence_path.exists():
            raise GuidedBuildError("capability completion requires evidence")
        report = validate_evidence(evidence_path, args.contract)
        if not report["valid"]:
            raise GuidedBuildError("evidence is invalid: " + "; ".join(report["errors"]))
        if report["metadata"].get("milestone_id") != args.milestone:
            raise GuidedBuildError("evidence belongs to another milestone")
        if args.capability not in report["metadata"].get("completed_capabilities", []):
            raise GuidedBuildError("evidence must list the capability as completed")
    capability = milestone["capabilities"][args.capability]
    capability["delivery_status"] = args.status
    now = utc_now()
    if args.status == "in_progress":
        capability.setdefault("started_at", now)
        milestone["active_capability"] = args.capability
    elif args.status == "complete":
        capability.setdefault("started_at", now)
        capability["completed_at"] = now
        if milestone.get("active_capability") == args.capability:
            milestone["active_capability"] = None
    elif milestone.get("active_capability") == args.capability and args.status == "not_started":
        milestone["active_capability"] = None
    state["updated_at"] = now
    atomic_json(location, state)
    print(
        json.dumps(
            {
                "milestone": args.milestone,
                "capability": args.capability,
                "delivery_status": args.status,
            },
            indent=2,
        )
    )
    return 0


def set_preferences_command(args: argparse.Namespace) -> int:
    updates = {
        key: value
        for key, value in {
            "guidance": getattr(args, "guidance", None),
            "granularity": getattr(args, "granularity", None),
            "verbosity": getattr(args, "verbosity", None),
            "struggle": getattr(args, "struggle", None),
        }.items()
        if value is not None
    }
    if not updates:
        raise GuidedBuildError("set-preferences requires at least one preference flag")
    location, state, _ = load_state(args.contract, args.repo, create=True)
    state.setdefault("preferences", {}).update(updates)
    state["updated_at"] = utc_now()
    atomic_json(location, state)
    print(json.dumps({"preferences_updated": sorted(updates)}, indent=2))
    return 0


def normalize_topic(value: str) -> str:
    topic = re.sub(r"\s+", " ", value.strip())
    if not topic:
        raise GuidedBuildError("familiarity topic must not be empty")
    if len(topic) > 120:
        raise GuidedBuildError("familiarity topic must be at most 120 characters")
    return topic


def record_familiarity_command(args: argparse.Namespace) -> int:
    location, state, contract = load_state(args.contract, args.repo, create=True)
    if args.milestone not in contract["milestones"]:
        raise GuidedBuildError(f"unknown milestone {args.milestone}")
    topic = normalize_topic(args.topic)
    topics = state.setdefault("calibration_topics", {}).setdefault(args.milestone, {})
    topics[topic.casefold()] = {
        "topic": topic,
        "familiarity": args.level,
        "updated_at": utc_now(),
    }
    state["updated_at"] = utc_now()
    atomic_json(location, state)
    print(json.dumps({"milestone": args.milestone, "topic_recorded": True}, indent=2))
    return 0


def set_delivery_command(args: argparse.Namespace) -> int:
    location, state, contract = load_state(args.contract, args.repo)
    if args.milestone not in contract["milestones"]:
        raise GuidedBuildError(f"unknown milestone {args.milestone}")
    if args.status == "complete":
        incomplete_capabilities = [
            capability_id
            for capability_id, capability in state["milestones"][args.milestone]["capabilities"].items()
            if capability.get("delivery_status") != "complete"
        ]
        if incomplete_capabilities:
            raise GuidedBuildError(
                "milestone completion requires every capability complete: "
                + ", ".join(incomplete_capabilities)
            )
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
    if args.status == "complete" and state.get("active_milestone") == args.milestone:
        state["active_milestone"] = None
        item["active_slice"] = None
        item["active_capability"] = None
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
    familiarity = getattr(args, "familiarity", None)
    if familiarity is not None:
        concept["familiarity"] = familiarity
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
    exported = state if args.include_private_notes else redact_private_notes(state)
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
        backup_state(location)
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

    preferences = commands.add_parser("set-preferences")
    add_project_arguments(preferences)
    preferences.add_argument("--guidance", choices=sorted(GUIDANCE_STYLES))
    preferences.add_argument("--granularity", choices=sorted(GRANULARITY_STYLES))
    preferences.add_argument("--verbosity", choices=sorted(VERBOSITY_STYLES))
    preferences.add_argument("--struggle", choices=sorted(STRUGGLE_POLICIES))
    preferences.set_defaults(handler=set_preferences_command)

    familiarity = commands.add_parser("record-familiarity")
    add_project_arguments(familiarity)
    familiarity.add_argument("milestone")
    familiarity.add_argument("topic")
    familiarity.add_argument("level", choices=sorted(FAMILIARITY_LEVELS))
    familiarity.set_defaults(handler=record_familiarity_command)

    start = commands.add_parser("start-milestone")
    add_project_arguments(start)
    start.add_argument("milestone")
    start.add_argument("--depth", choices=sorted(DEPTHS), required=True)
    start.set_defaults(handler=start_milestone_command)

    capability_start = commands.add_parser("start-capability")
    add_project_arguments(capability_start)
    capability_start.add_argument("milestone")
    capability_start.add_argument("capability")
    capability_start.add_argument("--evidence", type=Path)
    capability_start.set_defaults(handler=start_capability_command)

    capability_delivery = commands.add_parser("set-capability-delivery")
    add_project_arguments(capability_delivery)
    capability_delivery.add_argument("milestone")
    capability_delivery.add_argument("capability")
    capability_delivery.add_argument("status", choices=sorted(DELIVERY_STATUSES))
    capability_delivery.add_argument("--evidence", type=Path)
    capability_delivery.set_defaults(handler=set_capability_delivery_command)

    delivery = commands.add_parser("set-delivery")
    add_project_arguments(delivery)
    delivery.add_argument("milestone")
    delivery.add_argument("status", choices=sorted(DELIVERY_STATUSES))
    delivery.add_argument("--evidence", type=Path)
    delivery.set_defaults(handler=set_delivery_command)

    concept = commands.add_parser("record-concept")
    add_project_arguments(concept)
    concept.add_argument("milestone")
    concept.add_argument("concept")
    concept.add_argument("mastery", choices=sorted(MASTERY_STATUSES))
    concept.add_argument("--evidence", action="append")
    concept.add_argument("--confidence", type=int, choices=range(1, 6))
    concept.add_argument("--familiarity", choices=sorted(FAMILIARITY_LEVELS))
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
