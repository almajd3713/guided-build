# Guided Build

Guided Build is a Codex plugin for learning software concepts while delivering real projects. It turns an existing plan into an approved learning contract, partitions each milestone by learning value and delivery risk, and keeps engineering evidence separate from private learner state.

Status: **0.1.0 beta**. The artifact schemas are versioned, but feedback-driven changes are expected before 1.0.

## Why it exists

Coding agents create a difficult trade-off: write everything yourself and move slowly, or delegate everything and lose the ability to explain the system. Guided Build provides three coordinated workflows:

1. **Onboard** a free-form roadmap into a reviewed contract.
2. **Build** one bounded milestone in Fast, Balanced, or Deep mode.
3. **Review/resume** through code tours, debugging evidence, and prerequisite-aware concept revisits.

It does not grade or certify learners. It records evidence that can be revisited.

## Install locally

From this repository:

```bash
codex plugin marketplace add .
codex plugin add guided-build@guided-build
```

Start a new Codex thread after installation, then ask:

```text
Use Guided Build to onboard this project from its roadmap.
```

The plugin has no required MCP servers, hosted service, account, or telemetry. Python 3.10 or newer is required for deterministic validation and private-state helpers.

## Project artifacts

Guided Build adds only shared, reviewable project artifacts:

```text
.guided-build/
├── project.md
└── evidence/
    └── <milestone-id>.md
```

`.guided-build/project.md` is the approved project-learning contract. Evidence documents contain repository facts, decisions, validation results, and accepted debt.

Familiarity, confidence, misconceptions, and session notes are stored outside the repository:

- Linux: `$XDG_STATE_HOME/guided-build` or `~/.local/state/guided-build`
- macOS: `~/Library/Application Support/Guided Build`
- Windows: `%LOCALAPPDATA%\Guided Build`

Set `GUIDED_BUILD_STATE_HOME` to override the state location.

## Depth modes

| Mode | Learner ownership | Agent ownership |
|---|---|---|
| Fast | One design prediction plus diagnostic review | Implementation and mechanical coverage |
| Balanced | At least one critical decision or implementation slice | Scaffolding, fixtures, wiring, repetitive coverage |
| Deep | Core behavior and primary test | Environment, scaffolding, mechanical integration, review |

Engineering checks never weaken when depth changes.

## State and validation CLI

Codex invokes `plugins/guided-build/scripts/guided_build.py`. It can also be used directly:

```bash
python3 plugins/guided-build/scripts/guided_build.py validate-contract /path/to/project/.guided-build/project.md
python3 plugins/guided-build/scripts/guided_build.py init-state --repo /path/to/project --contract /path/to/project/.guided-build/project.md
python3 plugins/guided-build/scripts/guided_build.py status --repo /path/to/project --contract /path/to/project/.guided-build/project.md
```

Status and exports redact familiarity and private notes by default. Import requires an explicit replacement flag when state already exists.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 /path/to/skill-creator/scripts/quick_validate.py plugins/guided-build/skills/guided-build-onboard
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/guided-build
```

See [architecture](docs/architecture.md), [privacy](docs/privacy.md), and [evaluation strategy](docs/evaluations.md).

## Current boundaries

- Software projects only; other technical and non-technical project types are not evaluated.
- Individual learner state only; team dashboards and centralized mastery reporting are excluded.
- External code graph, documentation, diagram, and GitHub tools are optional capabilities.
- The agent still requires user approval for destructive, external, or high-risk operations.
