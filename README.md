# Claude Code Skills

A collection of custom skills for Claude Code that extend its capabilities for architecture documentation, diagramming, and presentation styling.

## Skills

### arch-describe

*Plugin: architect*

Generate structured IT architecture descriptions with ASCII diagrams from short prompts.

**Usage**: Ask Claude to describe, explain, or document the architecture of any IT system.

**Output Structure**:
1. **Overview** - System purpose and high-level architecture
2. **Components** - List of all components with descriptions
3. **Connections** - Numbered list of integrations between components
4. **Diagram** - ASCII diagram with annotated connections

**Example**:
```
Describe the architecture of a Kafka cluster
```

Includes reference documentation for 20+ common systems including Kafka, Kubernetes, PostgreSQL HA, Redis Cluster, Elasticsearch, and more.

### arch-draw

*Plugin: architect*

Generate professional draw.io diagrams in XML format from architectural descriptions.

**Usage**: Ask Claude to create visual diagrams for system architecture, microservices, workflows, network topology, or data flows.

**Capabilities**:
- System architecture diagrams
- Microservices layouts
- Workflow/BPMN diagrams
- Network topology
- Data flow diagrams

**Features**:
- Grid-aligned layouts (10px grid)
- Arrow routing with collision avoidance
- Consistent color schemes
- Container/swimlane support
- Multiple architectural patterns (three-tier, event-driven, etc.)
- "studio" style preset (IBM Plex type, white boxes on tinted zones, colour only for meaning) — ask for "studio style"

**Example**:
```
Create a draw.io diagram for a microservices architecture with API Gateway, 3 services, message bus, and databases
```

### pptx-core-style

*Plugin: presentation*

Corporate presentation style guide for core principles architecture slides. Provides a canonical visual language — color palette, typography scale, layout grid, and component styles — to use alongside the `pptx` skill.

**Covers**: NAVY/BLUE/ORANGE/STEEL color tokens, two-column layout with divider, content blocks with badges, tables with accent rows, key insight blocks, distribution bars, category descriptions with colored emphasis.

**Example**:
```
Create an architecture slide using pptx-core-style with three numbered content blocks and a comparison table
```

### pptx-arch-style

*Plugin: presentation*

Architectural presentation style guide for architecture committee reviews. Defines a complete visual system adapted from a Google Slides "Modern Business" template.

**Covers**: title/section/content slide layouts, page number badge + red accent line, semantic status colors (done/planned/not verified), three table styles (checklist, status tracker, data), content boxes, numbered circles, category cards with left accent, stat callout funnels, flow and decision tree diagram conventions.

**Example**:
```
Create an architecture review deck using pptx-arch-style with a title slide, status tracker table, and flow diagram
```

### pptx-compare

*Plugin: presentation*

Compare two `.pptx` decks — structurally, by rendered pixels, or by dumping a single slide with exact numbers. Diagnostic and opinion-free: it measures the gap between two decks and calls neither correct. Use it to align a generator against a hand-made reference, to check a rebuilt deck against the previously committed one for regressions, or to read exact values off someone else's slide.

**Covers**: per-slide shape-by-shape diff (text by run, font, size, weight, color, fill, outline, alignment, indents, x/y/w/h in EMU) with cost-based shape matching and a `--pos-tol` coordinate tolerance; single-slide dump in EMU and inches; pixel diff of two render folders with red-highlight overlays, a contact sheet, and `--zoom`. `--render` needs `soffice` and `pdftoppm`; the structural comparison needs neither. Known PowerPoint/pptxgenjs engine artefacts are documented in `references/engine-differences.md`.

**Example**:
```
Compare the generated deck against the reference and tell me what still differs
```

### offdesk

*Plugin: obsidian*

Push markdown files from any project into an Obsidian vault on phone/tablet for off-desk reading, then pull annotated `>[!ai]` callouts back to the source file. Two transports carry the vault: **syncthing** (P2P, the default — no cloud, no bot) and **icloud** (an Obsidian vault in iCloud Drive, for iPad). A push goes to exactly one transport; a pull scans both by default and tags each finding with its transport and the vault copy's age.

**Usage**: Ask Claude to send a doc to offdesk for review, or to check feedback from your phone. Name iCloud in the phrase to use that vault instead; vault roots come from `OFFDESK_SYNCTHING_VAULT` / `OFFDESK_ICLOUD_VAULT`.

**Example**:
```
положи это в offdesk
send to offdesk icloud
посмотри оффдеск фидбэк
check offdesk icloud
```

### pdf

*Plugin: publish*

Convert a markdown file to a PDF rendered with weasyprint, IBM Plex typography, and Obsidian-style heading anchors. Conversion-only — no upload, no transport. Sibling skills (e.g. `publish`) shell out to its script when they need a PDF.

**Usage**: Ask Claude to render a markdown file as a PDF.

**Example**:
```
convert this to pdf
render as pdf
сделай pdf
```

### publish

*Plugin: publish*

Publish a file from the active project to a configured transport provider: markdown is rendered to PDF, while ready-made artifacts (`.pdf`/`.pptx`/`.key`/`.docx`) are copied as-is (passthrough, no conversion). v1.4 ships three providers: `icloud` (iCloud Drive → tap to open in Books / Files / Preview on any signed-in device, override with `PUBLISH_ICLOUD_DIR`), `google-drive` (Google Drive for desktop mount; mount-only with multi-account hard-fail — set `PUBLISH_GOOGLE_DRIVE_DIR` to disambiguate when more than one account is signed in), and `onedrive` (OneDrive for Mac mount; same multi-account hard-fail for Personal alongside Work/School — set `PUBLISH_ONEDRIVE_DIR` to disambiguate). Push-only — pen marks stay with the human.

**Usage**: Ask Claude to send a doc to a transport for off-desk reading.

**Example**:
```
send to books
read on ipad
положи это в books
почитаю на айпаде
положи в icloud
send to gdrive
read on drive
положи в гугл драйв
send to onedrive
read on onedrive
положи в onedrive
```

### zmx-peer-chat

*Plugin: zmx-peer-chat*

Peer chat between a Claude Code session and a Codex session on the same Linux box, each in its own zmx session started by the box launcher, without agterm and without a connection back to the Mac. Claude sends with `codex queue` by the Codex thread's UUID, and only while the Codex pane shows that thread; Codex sends into Claude's private mailbox, and a wait run by the plugin's hooks wakes Claude in both Happy modes. The plugin ships a Claude skill, a Codex skill (installed with `codex plugin marketplace add`), a register helper for the launcher and an example Codex rules file. The contract and the box demonstrations are in `design/zmx-peer-chat.md`.

**Usage**: In a registered pair, ask either agent to chat with the other; messages arrive labelled `Chat from Claude:` / `Chat from Codex:`.

**Example**:
```
chat with codex about the failing test
talk to claude about this diff
```

### agent-chat

*Plugin: agent-chat*

Chat between agents on different hosts, and with the user, through the project's invite-only room on a private Matrix homeserver that only the VPN reaches. Every agent dials out, so a host behind NAT and a host that accepts no inbound connection both take part, and the user reads and answers the same room in Element. `agent-chat send` posts into the room; a wait run by the plugin's hooks wakes an idle interactive Claude session when a message addressed to its account arrives, labelled with its sender's authority (the user, a peer agent with no approval authority, or an unexpected sender). Codex sends in two steps through a prepared message file, and `agent-chat watch-codex`, a long-running process under the host's supervisor, queues each message addressed to the Codex account to a Codex thread with `codex queue`: the thread given with `--thread`, or the one zmx-peer-chat's launcher registered for the room's directory. The homeserver, accounts, rooms and each host's config come from provisioning; the plugin only reads them. See `plugins/agent-chat/README.md`.

**Usage**: On a provisioned host, in an onboarded project, ask Claude or Codex to message another agent or the room; replies addressed to this host's Claude account wake Claude, and those addressed to its Codex account arrive in Codex as a queued turn.

**Example**:
```
ask codex-b whether the migration finished
post this summary to the project room
```

## Project Structure

Skills are grouped by domain under `plugins/architect/skills/`, `plugins/presentation/skills/`, `plugins/obsidian/skills/`, `plugins/publish/skills/`, `plugins/zmx-peer-chat/skills/`, and `plugins/agent-chat/skills/`:

```
claude-skills/
├── .agents/plugins/
│   └── marketplace.json                          # Codex catalog (zmx-peer-chat, agent-chat)
├── .claude-plugin/
│   └── marketplace.json                          # Marketplace manifest
└── plugins/
    ├── architect/                                # plugins/architect/skills/
    │   ├── .claude-plugin/
    │   │   └── plugin.json                       # Plugin manifest
    │   └── skills/
    │       ├── arch-describe/
    │       │   ├── SKILL.md                      # Skill definition and instructions
    │       │   └── references/
    │       │       └── architectures.md          # Reference for 20+ common systems
    │       └── arch-draw/
    │           ├── SKILL.md                      # Skill definition and instructions
    │           ├── references/
    │           │   ├── cheatsheet.md             # Quick reference for XML elements
    │           │   ├── agent-prompt.md           # Prompt templates and validation
    │           │   └── style-studio.md           # Studio style preset: palette, fonts, styles
    │           └── assets/
    │               ├── studio-example.drawio     # Studio example: "Who reads what"
    │               ├── studio-kafka-example.drawio  # Studio example: Kafka platform
    │               └── studio-bpmn-example.drawio   # Studio example: BPMN order process
    ├── presentation/                             # plugins/presentation/skills/
    │   ├── .claude-plugin/
    │   │   └── plugin.json                       # Plugin manifest
    │   └── skills/
    │       ├── pptx-core-style/
    │       │   └── SKILL.md                      # Style guide for core architecture slides
    │       ├── pptx-arch-style/
    │       │   └── SKILL.md                      # Style guide for architecture committee decks
    │       └── pptx-compare/
    │           ├── SKILL.md                      # Skill definition and instructions
    │           ├── references/
    │           │   └── engine-differences.md     # PowerPoint vs pptxgenjs artefacts
    │           └── scripts/
    │               ├── compare_decks.py          # Shape-by-shape diff of two decks
    │               ├── dump_slide.py             # One slide as exact numbers
    │               ├── pixel_diff.py             # Pixel diff of two render folders
    │               └── tests/                    # Pytest suite + fixture decks
    ├── obsidian/                                 # plugins/obsidian/skills/
    │   ├── .claude-plugin/
    │   │   └── plugin.json                       # Plugin manifest
    │   └── skills/
    │       └── offdesk/
    │           ├── SKILL.md                      # Skill definition and instructions
    │           ├── references/
    │           │   ├── transports.md             # Transport table (env vars, default roots)
    │           │   └── setup.md                  # Syncthing, iCloud + Obsidian manual setup
    │           ├── scripts/
    │           │   ├── transports.py             # Trigger → transport routing
    │           │   └── merge-frontmatter.py      # offdesk-* frontmatter merge
    │           └── tests/
    │               ├── test_transports.py        # Trigger + vault-root resolver tests
    │               └── test_trigger_collisions.py  # offdesk vs publish vocabulary guard
    ├── zmx-peer-chat/                            # plugins/zmx-peer-chat/skills/
    │   ├── .claude-plugin/
    │   │   └── plugin.json                       # Claude plugin manifest
    │   ├── .codex-plugin/
    │   │   └── plugin.json                       # Codex plugin manifest
    │   ├── bin/zmx-peer-chat                     # The command (register, send, wait, ...)
    │   ├── hooks/hooks.json                      # Claude hooks that run the wait
    │   ├── codex/
    │   │   ├── hooks.json                        # Empty: keeps the Claude hooks out of Codex
    │   │   └── rules/zmx-peer-chat.rules         # Example Codex prefix rules
    │   ├── codex-skills/zmx-peer-chat/
    │   │   └── SKILL.md                          # Codex side
    │   └── skills/zmx-peer-chat/
    │       ├── SKILL.md                          # Claude side
    │       ├── scripts/zpc/                      # Router, mailbox, register helper, daemon client
    │       └── tests/                            # Pytest suite with zmx and daemon fakes
    ├── agent-chat/                               # plugins/agent-chat/skills/
    │   ├── .claude-plugin/
    │   │   └── plugin.json                       # Claude plugin manifest
    │   ├── .codex-plugin/
    │   │   └── plugin.json                       # Codex plugin manifest
    │   ├── bin/agent-chat                        # The command (send, hook-wait, watch-codex, ...)
    │   ├── hooks/hooks.json                      # Claude hooks that run the wait
    │   ├── codex/
    │   │   ├── hooks.json                        # Empty: keeps the Claude hooks out of Codex
    │   │   └── rules/agent-chat.rules            # Example Codex prefix rules
    │   ├── codex-skills/agent-chat/
    │   │   └── SKILL.md                          # Codex side
    │   └── skills/agent-chat/
    │       ├── SKILL.md                          # Claude side
    │       ├── scripts/agent_chat/               # Matrix client, room, sync loop, Codex watcher
    │       └── tests/                            # Pytest suite with homeserver, proxy, codex, zmx fakes
    └── publish/                                  # plugins/publish/skills/
        ├── .claude-plugin/
        │   └── plugin.json                       # Plugin manifest
        └── skills/
            ├── pdf/
            │   ├── SKILL.md                      # Conversion-only MD → PDF skill
            │   ├── references/
            │   │   └── styles.css                # PDF styling (typography, page breaks)
            │   ├── scripts/
            │   │   └── md-to-pdf.py              # Markdown → PDF converter
            │   └── tests/
            │       └── test_anchors.py           # Obsidian-anchor resolution tests
            └── publish/
                ├── SKILL.md                      # Umbrella push skill
                ├── references/
                │   ├── providers.md              # Provider table (env vars, default roots)
                │   └── icloud.md                 # iCloud-as-transport notes
                ├── scripts/
                │   └── providers.py              # Trigger → provider routing
                └── tests/
                    └── test_providers.py         # Trigger + env-var resolver tests
```

## Installation

These skills are distributed as Claude Code plugins via a marketplace.

### One-time setup

```
/plugin marketplace add https://github.com/dddpaul/claude-skills
```

### Install the plugins you want

```
/plugin install architect@dddpaul-claude-skills      # arch-describe + arch-draw
/plugin install presentation@dddpaul-claude-skills   # pptx-core-style + pptx-arch-style + pptx-compare
/plugin install obsidian@dddpaul-claude-skills       # offdesk
/plugin install publish@dddpaul-claude-skills        # pdf + publish
/plugin install zmx-peer-chat@dddpaul-claude-skills  # zmx-peer-chat (Claude side, Linux box)
/plugin install agent-chat@dddpaul-claude-skills     # agent-chat (Claude side, any provisioned host)
```

The Codex sides of zmx-peer-chat and agent-chat install from a clone of this repo with `codex plugin marketplace add <clone>` and `codex plugin add zmx-peer-chat@dddpaul-claude-skills` or `codex plugin add agent-chat@dddpaul-claude-skills`; see each plugin's README for the `PATH` and rules it also needs, and agent-chat's for its watcher.

### Update later

```
/plugin marketplace update dddpaul-claude-skills
```

## Creating New Skills

Each skill follows this structure:

```
plugins/<domain>/skills/<skill-name>/
├── SKILL.md           # Required: frontmatter + body
└── references/        # Optional
    └── *.md
```

If the skill belongs to a new domain (e.g., `obsidian`), create a new `plugins/<domain>/` with its own `.claude-plugin/plugin.json` and register it in the root `.claude-plugin/marketplace.json`.

The `SKILL.md` file must include YAML frontmatter:

```yaml
---
name: skill-name
description: Brief description of when to use this skill
---
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
