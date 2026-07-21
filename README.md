# Guided Build

Guided Build is a Codex plugin for learning software concepts while delivering real projects. It turns an existing plan into an approved capability-based learning contract, partitions work by learning value and delivery risk, and keeps engineering evidence separate from private learner state.

Status: **0.1.0-beta.3**. This release introduces contract/evidence v2 and capability-level progress. Regenerate v1 onboarding contracts before continuing; private v1 state migrates automatically with a backup.

## Why it exists

Coding agents create a difficult trade-off: write everything yourself and move slowly, or delegate everything and lose the ability to explain the system. Guided Build provides three coordinated workflows:

1. **Onboard** a free-form roadmap into a reviewed contract.
2. **Build** one cohesive capability at a time inside a Fast, Balanced, or Deep milestone.
3. **Review/resume** through code tours, debugging evidence, and prerequisite-aware concept revisits.

It does not grade or certify learners. It records evidence that can be revisited.

## Installation

Install Guided Build from its public GitHub marketplace:

```bash
codex plugin marketplace add almajd3713/guided-build
codex plugin add guided-build@guided-build
```

Start a new Codex session after installation so the bundled skills are loaded. In Codex CLI, you can also run `/plugins` after adding the marketplace and install **Guided Build** interactively.

To update an existing installation:

```bash
codex plugin marketplace upgrade guided-build
codex plugin add guided-build@guided-build
```

Then start another new Codex session.

For local plugin development from a repository checkout instead:

```bash
codex plugin marketplace add .
codex plugin add guided-build@guided-build
```

The plugin has no required MCP servers, hosted service, account, or telemetry. Python 3.10 or newer is required for deterministic validation and private-state helpers.

## Usage and prompts

Guided Build has three lifecycle workflows. Invoke the one matching the current project state.

### 1. Onboard a project

Use this when the project has a roadmap, specification, issue list, README, or other plan but does not yet have an approved `.guided-build/project.md`:

```text
Use Guided Build to onboard this project from its roadmap.
```

Name the source files when you know them:

```text
Use Guided Build to onboard this project using README.md and docs/roadmap.md.
```

Onboarding creates a draft learning contract and stops for your review. It does not begin implementation or approve the contract for you.

### 2. Start or continue a milestone

After approving the contract, start the next eligible milestone:

```text
Start my next Guided Build milestone in Balanced mode.
```

You can select a milestone and depth explicitly:

```text
Start M02 in Fast mode.
Start M03 in Deep mode and teach unfamiliar prerequisites before assigning my work.
Continue the active Guided Build milestone using example-first guidance.
Continue the active Guided Build capability in Lean granularity and compact verbosity.
```

Fast, Balanced, and Deep change learner ownership, not engineering validation. The milestone workflow checks concept readiness before assigning niche or unfamiliar work.

Granularity is separate from depth:

- **Lean** keeps the capability outcome but normally uses at most two pedagogical gates.
- **Adaptive** (default) spends gates where current evidence shows learning value; a third gate is reserved for high-risk work or an explicit request to go deeper.
- **Thorough** allows up to four gates for extra retrieval and counterexamples.

Verbosity controls response length independently. For example:

```text
Continue in Balanced depth, Lean granularity, and compact verbosity.
Continue in Deep depth with Thorough granularity and example-first guidance.
Use Adaptive granularity and reuse what I already demonstrated instead of repeating familiarity checks.
```

### 3. Review, resume, or reconcile

Use review after completing a slice or when you want to verify your understanding:

```text
Review my current Guided Build milestone.
```

Use resume in a later session or after an interruption:

```text
Resume this Guided Build project.
Resume this Guided Build project and reconcile the unfinished milestone evidence.
Review the active milestone and revisit any prerequisite concepts that are due.
```

Review keeps capability delivery and mastery separate, reuses accepted learning evidence instead of adding a ritual final quiz, reconciles repository behavior with existing evidence, and preserves private learning notes outside the repository.

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

Coaching preferences are also private. Guided Build defaults to an efficient loop—one diagnostic, a compact example only when needed, one focused task, and one acceptance check—and can remember explicit guidance, granularity, verbosity, and struggle choices per project.

## Depth modes

| Mode | Learner ownership | Agent ownership |
|---|---|---|
| Fast | One design prediction plus diagnostic review | Implementation and mechanical coverage |
| Balanced | At least one critical decision or implementation slice | Scaffolding, fixtures, wiring, repetitive coverage |
| Deep | Core behavior and primary test | Environment, scaffolding, mechanical integration, review |

Engineering checks never weaken when depth changes.

Capabilities are stable contract units such as `M00.C01`. They group related implementation and tests around one observable outcome. They are intentionally larger than one function or API operation, so progress is forecastable without repeated micro-briefings.

## State and validation CLI

Codex invokes `plugins/guided-build/scripts/guided_build.py`. It can also be used directly:

```bash
python3 plugins/guided-build/scripts/guided_build.py validate-contract /path/to/project/.guided-build/project.md
python3 plugins/guided-build/scripts/guided_build.py init-state --repo /path/to/project --contract /path/to/project/.guided-build/project.md
python3 plugins/guided-build/scripts/guided_build.py status --repo /path/to/project --contract /path/to/project/.guided-build/project.md
python3 plugins/guided-build/scripts/guided_build.py set-preferences --repo /path/to/project --guidance execution_first --granularity lean --verbosity compact --struggle offer_choices
python3 plugins/guided-build/scripts/guided_build.py record-familiarity M01 "unsigned integer codecs" new --repo /path/to/project
python3 plugins/guided-build/scripts/guided_build.py start-capability M01 M01.C01 --repo /path/to/project
python3 plugins/guided-build/scripts/guided_build.py set-capability-delivery M01 M01.C01 complete --repo /path/to/project
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
