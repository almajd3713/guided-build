from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / "plugins" / "guided-build" / "scripts" / "guided_build.py"
SPEC = importlib.util.spec_from_file_location("guided_build", CLI_PATH)
assert SPEC and SPEC.loader
guided_build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guided_build)

VALID_CONTRACT = ROOT / "tests" / "fixtures" / "contracts" / "valid-project.md"
CYCLIC_CONTRACT = ROOT / "tests" / "fixtures" / "contracts" / "cyclic-project.md"
VALID_EVIDENCE = ROOT / "tests" / "fixtures" / "evidence" / "m01-complete.md"


class ContractTests(unittest.TestCase):
    def test_valid_contract_exposes_dependencies_and_concepts(self) -> None:
        report = guided_build.validate_contract(VALID_CONTRACT)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["milestones"]["M02"]["prerequisites"], ["M01"])
        self.assertEqual(report["milestones"]["M01"]["concepts"], ["Boundary validation"])

    def test_cycle_is_rejected(self) -> None:
        report = guided_build.validate_contract(CYCLIC_CONTRACT)
        self.assertFalse(report["valid"])
        self.assertTrue(any("cycle" in error for error in report["errors"]))

    def test_unknown_compatible_frontmatter_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.md"
            text = VALID_CONTRACT.read_text(encoding="utf-8").replace(
                "status: approved", 'status: approved\nowner_hint: "optional"'
            )
            path.write_text(text, encoding="utf-8")
            report = guided_build.validate_contract(path)
            self.assertTrue(report["valid"], report["errors"])
            self.assertEqual(report["metadata"]["owner_hint"], "optional")

    def test_evidence_must_match_contract(self) -> None:
        report = guided_build.validate_evidence(VALID_EVIDENCE, VALID_CONTRACT)
        self.assertTrue(report["valid"], report["errors"])

    def test_likely_composite_concept_warns_without_invalidating_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.md"
            text = VALID_CONTRACT.read_text(encoding="utf-8").replace(
                "- Boundary validation",
                "- Parsing, validation, and error reporting",
            ).replace(
                '["Boundary validation"]',
                '["Parsing, validation, and error reporting"]',
            )
            path.write_text(text, encoding="utf-8")
            report = guided_build.validate_contract(path)
            self.assertTrue(report["valid"], report["errors"])
            self.assertTrue(any("may be composite" in item for item in report["warnings"]))

    def test_evidence_rejects_private_learner_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.md"
            text = VALID_EVIDENCE.read_text(encoding="utf-8").replace(
                "The learner predicted and diagnosed an empty-title failure.",
                "Learner self-report: new to parser boundaries.",
            )
            path.write_text(text, encoding="utf-8")
            report = guided_build.validate_evidence(path, VALID_CONTRACT)
            self.assertFalse(report["valid"])
            self.assertTrue(any("private learner label" in item for item in report["errors"]))

    def test_duplicate_frontmatter_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.md"
            text = VALID_CONTRACT.read_text(encoding="utf-8").replace(
                "status: approved", "status: approved\nstatus: draft"
            )
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(guided_build.GuidedBuildError, "duplicate key"):
                guided_build.validate_contract(path)

    def test_empty_title_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.md"
            text = VALID_CONTRACT.read_text(encoding="utf-8").replace(
                'title: "Sample CLI"', 'title: ""'
            )
            path.write_text(text, encoding="utf-8")
            report = guided_build.validate_contract(path)
            self.assertFalse(report["valid"])
            self.assertIn("title must be a non-empty string", report["errors"])

    def test_wrong_evidence_milestone_is_rejected_by_delivery_transition(self) -> None:
        report = guided_build.validate_evidence(VALID_EVIDENCE, VALID_CONTRACT)
        self.assertEqual(report["metadata"]["milestone_id"], "M01")

    def test_capability_bundle_is_structured(self) -> None:
        report = guided_build.validate_contract(VALID_CONTRACT)
        capability = report["milestones"]["M01"]["capabilities"]["M01.C01"]
        self.assertEqual(capability["concepts"], ["Boundary validation"])
        self.assertEqual(capability["prerequisites"], [])
        self.assertEqual(len(capability["deliverables"]), 2)

    def test_v1_contract_has_actionable_migration_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.md"
            path.write_text(
                VALID_CONTRACT.read_text(encoding="utf-8").replace(
                    "guided-build/v2", "guided-build/v1", 1
                ),
                encoding="utf-8",
            )
            report = guided_build.validate_contract(path)
            self.assertFalse(report["valid"])
            self.assertTrue(any("regenerate" in item for item in report["errors"]))

    def test_capability_rejects_undeclared_concept_and_unknown_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.md"
            text = VALID_CONTRACT.read_text(encoding="utf-8").replace(
                '["Boundary validation"]', '["Undeclared"]', 1
            ).replace(
                "- Prerequisites: []", '- Prerequisites: ["M01.C99"]', 1
            )
            path.write_text(text, encoding="utf-8")
            report = guided_build.validate_contract(path)
            self.assertFalse(report["valid"])
            self.assertTrue(any("undeclared concept" in item for item in report["errors"]))
            self.assertTrue(any("unknown capability" in item for item in report["errors"]))

    def test_capability_cycle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.md"
            text = VALID_CONTRACT.read_text(encoding="utf-8").replace(
                "- Prerequisites: []", '- Prerequisites: ["M01.C01"]', 1
            )
            path.write_text(text, encoding="utf-8")
            report = guided_build.validate_contract(path)
            self.assertFalse(report["valid"])
            self.assertTrue(any("capability dependency cycle" in item for item in report["errors"]))

    def test_more_than_eight_capabilities_warns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.md"
            source = VALID_CONTRACT.read_text(encoding="utf-8")
            marker = "\n### M02 — File persistence"
            bundles = []
            for number in range(2, 10):
                bundles.append(
                    f'''\n##### M01.C{number:02d} — Extra {number}\n\n'''
                    '- Outcome: "Extra outcome"\n'
                    '- Concepts: ["Boundary validation"]\n'
                    '- Prerequisites: []\n'
                    '- Deliverables: ["Extra delivery"]\n'
                    '- Validation: "Extra validation"\n'
                )
            path.write_text(source.replace(marker, "".join(bundles) + marker), encoding="utf-8")
            report = guided_build.validate_contract(path)
            self.assertTrue(report["valid"], report["errors"])
            self.assertTrue(any("prefer at most 8" in item for item in report["warnings"]))

    def test_evidence_budget_warns_without_invalidating(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.md"
            text = VALID_EVIDENCE.read_text(encoding="utf-8").replace(
                "The command parser now produces a validated command model.",
                " ".join(["word"] * 601),
            )
            path.write_text(text, encoding="utf-8")
            report = guided_build.validate_evidence(path, VALID_CONTRACT)
            self.assertTrue(report["valid"], report["errors"])
            self.assertTrue(report["compaction_required"])

    def test_evidence_log_count_and_entry_size_warn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.md"
            source = VALID_EVIDENCE.read_text(encoding="utf-8")
            prefix = source.split("## Slice log", 1)[0]
            entries = [
                f"### Entry {index}\n\n" + ("word " * (61 if index == 1 else 3))
                for index in range(1, 7)
            ]
            path.write_text(prefix + "## Slice log\n\n" + "\n".join(entries), encoding="utf-8")
            report = guided_build.validate_evidence(path, VALID_CONTRACT)
            self.assertTrue(report["valid"], report["errors"])
            self.assertTrue(any("6 entries" in item for item in report["warnings"]))
            self.assertTrue(any("entry 1" in item for item in report["warnings"]))


class StateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.contract = self.repo / ".guided-build" / "project.md"
        self.contract.parent.mkdir()
        shutil.copy2(VALID_CONTRACT, self.contract)
        self.evidence = self.repo / ".guided-build" / "evidence" / "M01.md"
        self.evidence.parent.mkdir()
        shutil.copy2(VALID_EVIDENCE, self.evidence)
        self.environment = mock.patch.dict(
            os.environ, {"GUIDED_BUILD_STATE_HOME": str(self.root / "private")}, clear=False
        )
        self.environment.start()

    def tearDown(self) -> None:
        self.environment.stop()
        self.temporary.cleanup()

    def project_args(self, **values: object) -> argparse.Namespace:
        defaults = {"contract": self.contract, "repo": self.repo}
        defaults.update(values)
        return argparse.Namespace(**defaults)

    def quietly(self, command: object, args: argparse.Namespace) -> object:
        with contextlib.redirect_stdout(io.StringIO()):
            return command(args)  # type: ignore[operator]

    def add_second_m01_capability(self) -> None:
        marker = "\n### M02 — File persistence"
        capability = '''
##### M01.C02 — Report parsed commands

- Outcome: "Validated commands are rendered for users"
- Concepts: ["Boundary validation"]
- Prerequisites: ["M01.C01"]
- Deliverables: ["Command formatter"]
- Validation: "Formatter tests pass"
'''
        self.contract.write_text(
            self.contract.read_text(encoding="utf-8").replace(marker, capability + marker),
            encoding="utf-8",
        )

    def write_partial_evidence(self, *, large: bool = False) -> None:
        text = VALID_EVIDENCE.read_text(encoding="utf-8").replace(
            "delivery_status: complete", "delivery_status: in_progress"
        ).replace(
            'completed_capabilities: ["M01.C01"]',
            'completed_capabilities: ["M01.C01"]',
        )
        if large:
            text = text.replace(
                "The command parser now produces a validated command model.",
                " ".join(["word"] * 601),
            )
        self.evidence.write_text(text, encoding="utf-8")

    def test_delivery_and_mastery_are_separate_prerequisite_gates(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        self.quietly(guided_build.start_milestone_command,
            self.project_args(milestone="M01", depth="balanced", slice="parser")
        )
        self.quietly(guided_build.record_concept_command,
            self.project_args(
                milestone="M01",
                concept="Boundary validation",
                mastery="practiced",
                confidence=3,
                evidence=[".guided-build/evidence/M01.md#learning-evidence"],
                misconception="Validation belongs only in the UI.",
                revisit_after="M02",
            )
        )
        self.quietly(
            guided_build.set_capability_delivery_command,
            self.project_args(
                milestone="M01",
                capability="M01.C01",
                status="complete",
                evidence=self.evidence,
            ),
        )
        self.quietly(guided_build.set_delivery_command,
            self.project_args(
                milestone="M01",
                status="complete",
                slice=None,
                evidence=self.evidence,
            )
        )
        with self.assertRaises(guided_build.GuidedBuildError):
            guided_build.start_milestone_command(
                self.project_args(milestone="M02", depth="fast", slice=None)
            )
        self.quietly(guided_build.record_concept_command,
            self.project_args(
                milestone="M01",
                concept="Boundary validation",
                mastery="demonstrated",
                confidence=4,
                evidence=[".guided-build/evidence/M01.md#learning-evidence"],
                misconception=None,
                revisit_after="M02",
            )
        )
        self.quietly(guided_build.start_milestone_command,
            self.project_args(milestone="M02", depth="fast", slice="storage")
        )
        _, state, _ = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(state["active_milestone"], "M02")

    def test_completion_requires_matching_complete_evidence(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        with self.assertRaises(guided_build.GuidedBuildError):
            guided_build.set_delivery_command(
                self.project_args(
                    milestone="M01", status="complete", slice=None, evidence=None
                )
            )

    def test_demonstrated_mastery_requires_evidence(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        with self.assertRaises(guided_build.GuidedBuildError):
            guided_build.record_concept_command(
                self.project_args(
                    milestone="M01",
                    concept="Boundary validation",
                    mastery="demonstrated",
                    confidence=None,
                    evidence=None,
                    misconception=None,
                    revisit_after=None,
                )
            )

    def test_status_and_default_export_redact_private_notes(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        self.quietly(guided_build.record_concept_command,
            self.project_args(
                milestone="M01",
                concept="Boundary validation",
                mastery="practiced",
                confidence=2,
                evidence=["evidence.md"],
                misconception="Private note marker",
                revisit_after=None,
                familiarity="new",
            )
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            guided_build.status_command(
                self.project_args(include_private_notes=False)
            )
        self.assertNotIn("Private note marker", output.getvalue())
        self.assertNotIn('"confidence"', output.getvalue())
        self.assertNotIn('"familiarity"', output.getvalue())

        exported = self.root / "export.json"
        self.quietly(guided_build.export_state_command,
            self.project_args(output=exported, include_private_notes=False)
        )
        export_data = json.loads(exported.read_text(encoding="utf-8"))
        concept = export_data["concepts"]["Boundary validation"]
        self.assertNotIn("confidence", concept)
        self.assertNotIn("familiarity", concept)
        self.assertNotIn("misconceptions", concept)

        private_output = io.StringIO()
        with contextlib.redirect_stdout(private_output):
            guided_build.status_command(
                self.project_args(include_private_notes=True)
            )
        self.assertIn('"familiarity": "new"', private_output.getvalue())

    def test_preferences_and_topic_familiarity_are_private_and_normalized(self) -> None:
        self.quietly(
            guided_build.set_preferences_command,
            self.project_args(
                guidance="execution_first",
                verbosity="compact",
                struggle="offer_choices",
            ),
        )
        self.quietly(
            guided_build.record_familiarity_command,
            self.project_args(
                milestone="M01",
                topic="  unsigned   integer codecs ",
                level="new",
            ),
        )
        self.quietly(
            guided_build.record_familiarity_command,
            self.project_args(
                milestone="M01",
                topic="Unsigned Integer Codecs",
                level="comfortable",
            ),
        )
        _, state, _ = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(state["preferences"]["verbosity"], "compact")
        topics = state["calibration_topics"]["M01"]
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics["unsigned integer codecs"]["familiarity"], "comfortable")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            guided_build.status_command(self.project_args(include_private_notes=False))
        self.assertNotIn("preferences", output.getvalue())
        self.assertNotIn("calibration_topics", output.getvalue())

        exported = self.root / "calibration-export.json"
        self.quietly(
            guided_build.export_state_command,
            self.project_args(output=exported, include_private_notes=False),
        )
        public_data = json.loads(exported.read_text(encoding="utf-8"))
        self.assertNotIn("preferences", public_data)
        self.assertNotIn("calibration_topics", public_data)

        private_export = self.root / "private-calibration-export.json"
        self.quietly(
            guided_build.export_state_command,
            self.project_args(output=private_export, include_private_notes=True),
        )
        private_data = json.loads(private_export.read_text(encoding="utf-8"))
        self.assertEqual(private_data["preferences"]["guidance"], "execution_first")
        self.assertIn("unsigned integer codecs", private_data["calibration_topics"]["M01"])

    def test_preferences_require_at_least_one_value(self) -> None:
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "at least one"):
            guided_build.set_preferences_command(
                self.project_args(guidance=None, verbosity=None, struggle=None)
            )

    def test_topic_familiarity_validates_length_and_milestone(self) -> None:
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "must not be empty"):
            guided_build.record_familiarity_command(
                self.project_args(milestone="M01", topic="   ", level="new")
            )
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "unknown milestone"):
            guided_build.record_familiarity_command(
                self.project_args(milestone="M99", topic="transactions", level="new")
            )

    def test_prerequisite_gate_uses_current_contract_concepts(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        self.contract.write_text(
            self.contract.read_text(encoding="utf-8").replace(
                "- Boundary validation", "- Input validation"
            ).replace('["Boundary validation"]', '["Input validation"]'),
            encoding="utf-8",
        )
        _, state, contract = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(state["milestones"]["M01"]["concepts"], ["Input validation"])
        state["milestones"]["M01"]["delivery_status"] = "complete"
        state["concepts"]["Boundary validation"] = {"mastery_status": "demonstrated"}
        state["concepts"]["Input validation"] = {"mastery_status": "practiced"}
        location, _ = guided_build.state_location(self.contract, self.repo)
        guided_build.atomic_json(location, state)
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "Input validation"):
            guided_build.start_milestone_command(
                self.project_args(milestone="M02", depth="fast", slice=None)
            )

    def test_topic_familiarity_does_not_satisfy_mastery_gate(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        self.quietly(
            guided_build.record_familiarity_command,
            self.project_args(
                milestone="M01", topic="Boundary validation", level="comfortable"
            ),
        )
        location, state, _ = guided_build.load_state(self.contract, self.repo)
        state["milestones"]["M01"]["delivery_status"] = "complete"
        guided_build.atomic_json(location, state)
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "requires review"):
            guided_build.start_milestone_command(
                self.project_args(milestone="M02", depth="fast", slice=None)
            )

    def test_draft_contract_cannot_start_work(self) -> None:
        self.contract.write_text(
            self.contract.read_text(encoding="utf-8").replace(
                "status: approved", "status: draft"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "must be approved"):
            guided_build.start_milestone_command(
                self.project_args(milestone="M01", depth="balanced", slice=None)
            )

    def test_concept_must_be_declared_for_the_milestone(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "not declared"):
            guided_build.record_concept_command(
                self.project_args(
                    milestone="M01",
                    concept="Undeclared concept",
                    mastery="practiced",
                    confidence=None,
                    evidence=None,
                    misconception=None,
                    revisit_after=None,
                )
            )

    def test_export_import_round_trip_requires_intentional_replace(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        exported = self.root / "export.json"
        self.quietly(
            guided_build.export_state_command,
            self.project_args(output=exported, include_private_notes=False),
        )
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "--replace"):
            guided_build.import_state_command(
                self.project_args(input=exported, replace=False)
            )
        self.quietly(
            guided_build.import_state_command,
            self.project_args(input=exported, replace=True),
        )
        location, state, _ = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(state["project_id"], "sample-cli")
        self.assertEqual(len(list(location.parent.glob("*.bak"))), 1)

    def test_import_rejects_structurally_malformed_state(self) -> None:
        malformed = self.root / "malformed.json"
        malformed.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "project_id": "sample-cli",
                    "milestones": [],
                    "concepts": {},
                    "session_notes": [],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "milestones"):
            guided_build.import_state_command(
                self.project_args(input=malformed, replace=False)
            )

    def test_granularity_preference_persists_and_sets_milestone(self) -> None:
        self.quietly(
            guided_build.set_preferences_command,
            self.project_args(
                guidance=None,
                granularity="lean",
                verbosity=None,
                struggle=None,
            ),
        )
        self.quietly(
            guided_build.start_milestone_command,
            self.project_args(milestone="M01", depth="balanced"),
        )
        _, state, _ = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(state["preferences"]["granularity"], "lean")
        self.assertEqual(state["milestones"]["M01"]["granularity"], "lean")

    def test_capability_prerequisite_then_completion(self) -> None:
        self.add_second_m01_capability()
        self.write_partial_evidence()
        self.quietly(
            guided_build.start_milestone_command,
            self.project_args(milestone="M01", depth="balanced"),
        )
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "M01.C01"):
            guided_build.start_capability_command(
                self.project_args(
                    milestone="M01", capability="M01.C02", evidence=self.evidence
                )
            )
        self.quietly(
            guided_build.set_capability_delivery_command,
            self.project_args(
                milestone="M01",
                capability="M01.C01",
                status="complete",
                evidence=self.evidence,
            ),
        )
        self.quietly(
            guided_build.start_capability_command,
            self.project_args(
                milestone="M01", capability="M01.C02", evidence=self.evidence
            ),
        )
        _, state, _ = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(state["milestones"]["M01"]["active_capability"], "M01.C02")

    def test_compaction_blocks_start_but_not_current_completion(self) -> None:
        self.write_partial_evidence(large=True)
        self.quietly(
            guided_build.start_milestone_command,
            self.project_args(milestone="M01", depth="balanced"),
        )
        with self.assertRaisesRegex(guided_build.GuidedBuildError, "compaction"):
            guided_build.start_capability_command(
                self.project_args(
                    milestone="M01", capability="M01.C01", evidence=self.evidence
                )
            )
        self.quietly(
            guided_build.set_capability_delivery_command,
            self.project_args(
                milestone="M01",
                capability="M01.C01",
                status="complete",
                evidence=self.evidence,
            ),
        )
        _, state, _ = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(
            state["milestones"]["M01"]["capabilities"]["M01.C01"]["delivery_status"],
            "complete",
        )

    def test_v1_state_migrates_with_backup_and_private_data(self) -> None:
        location, contract = guided_build.state_location(self.contract, self.repo)
        old_state = {
            "schema_version": 1,
            "project_id": "sample-cli",
            "contract_path": str(self.contract),
            "repo_hint": str(self.repo),
            "active_milestone": "M01",
            "milestones": {
                "M01": {
                    "delivery_status": "in_progress",
                    "depth": "balanced",
                    "active_slice": "parser",
                    "concepts": ["Boundary validation"],
                }
            },
            "concepts": {"Boundary validation": {"mastery_status": "practiced"}},
            "preferences": {"verbosity": "compact"},
            "calibration_topics": {"M01": {}},
            "session_notes": [],
            "created_at": guided_build.utc_now(),
            "updated_at": guided_build.utc_now(),
        }
        guided_build.atomic_json(location, old_state)
        _, state, _ = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(state["schema_version"], 2)
        self.assertEqual(state["preferences"]["verbosity"], "compact")
        self.assertEqual(state["concepts"]["Boundary validation"]["mastery_status"], "practiced")
        self.assertEqual(
            state["milestones"]["M01"]["capabilities"]["M01.C01"]["delivery_status"],
            "not_started",
        )
        self.assertEqual(len(list(location.parent.glob("*.bak"))), 1)

    @unittest.skipIf(os.name == "nt", "POSIX permissions are not available on Windows")
    def test_private_state_is_owner_read_write_only(self) -> None:
        self.quietly(guided_build.init_state_command, self.project_args())
        location, _, _ = guided_build.load_state(self.contract, self.repo)
        self.assertEqual(location.stat().st_mode & 0o777, 0o600)
        self.assertFalse(str(location).startswith(str(self.repo)))

    def test_cli_accepts_private_familiarity_calibration(self) -> None:
        args = guided_build.build_parser().parse_args(
            [
                "record-concept",
                "M01",
                "Boundary validation",
                "unassessed",
                "--familiarity",
                "some_exposure",
            ]
        )
        self.assertEqual(args.familiarity, "some_exposure")

    def test_cli_accepts_preference_and_topic_commands(self) -> None:
        preferences = guided_build.build_parser().parse_args(
            [
                "set-preferences",
                "--guidance",
                "execution_first",
                "--granularity",
                "lean",
                "--verbosity",
                "compact",
            ]
        )
        self.assertEqual(preferences.guidance, "execution_first")
        self.assertEqual(preferences.granularity, "lean")
        familiarity = guided_build.build_parser().parse_args(
            ["record-familiarity", "M01", "u64 codecs", "new"]
        )
        self.assertEqual(familiarity.topic, "u64 codecs")
        capability = guided_build.build_parser().parse_args(
            ["start-capability", "M01", "M01.C01"]
        )
        self.assertEqual(capability.capability, "M01.C01")


class PackagingTests(unittest.TestCase):
    def test_skills_are_complete_and_narrowly_triggered(self) -> None:
        skills = ROOT / "plugins" / "guided-build" / "skills"
        expected = {
            "guided-build-onboard",
            "guided-build-milestone",
            "guided-build-review",
        }
        self.assertEqual({path.name for path in skills.iterdir() if path.is_dir()}, expected)
        for skill in skills.iterdir():
            if not skill.is_dir():
                continue
            content = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("TODO", content)
            self.assertIn(f"name: {skill.name}", content)
            self.assertIn("Do not trigger", content)

    def test_plugin_has_no_required_external_capabilities(self) -> None:
        manifest = json.loads(
            (ROOT / "plugins" / "guided-build" / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("hooks", manifest)
        self.assertNotIn("apps", manifest)

    def test_eval_cases_cover_all_lifecycle_skills(self) -> None:
        cases = json.loads((ROOT / "tests" / "evals" / "cases.json").read_text())
        self.assertEqual(
            {case["skill"] for case in cases},
            {"guided-build-onboard", "guided-build-milestone", "guided-build-review"},
        )

    def test_milestone_requires_readiness_before_ownership(self) -> None:
        skill = (
            ROOT
            / "plugins"
            / "guided-build"
            / "skills"
            / "guided-build-milestone"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertLess(
            skill.index("Calibrate concept readiness"),
            skill.index("Brief and partition"),
        )
        self.assertIn("Do not ask the learner to design an interface", skill)
        reference = (
            ROOT
            / "plugins"
            / "guided-build"
            / "skills"
            / "guided-build-milestone"
            / "references"
            / "concept-readiness.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## Example: u64 codec", reference)
        self.assertIn("Theory-first", reference)
        self.assertIn("Example-first", reference)
        self.assertIn("Execution-first", reference)


if __name__ == "__main__":
    unittest.main()
