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

### offdesk

*Plugin: obsidian*

Push markdown files from any project into a Syncthing-synced Obsidian vault on phone/tablet for off-desk reading, then pull annotated `>[!ai]` callouts back to the source file. P2P only — no cloud, no bot.

**Usage**: Ask Claude to send a doc to offdesk for review, or to check feedback from your phone.

**Example**:
```
положи это в offdesk
посмотри оффдеск фидбэк
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

## Project Structure

Skills are grouped by domain under `plugins/architect/skills/`, `plugins/presentation/skills/`, `plugins/obsidian/skills/`, and `plugins/publish/skills/`:

```
claude-skills/
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
    │           └── references/
    │               ├── cheatsheet.md             # Quick reference for XML elements
    │               └── agent-prompt.md           # Prompt templates and validation
    ├── presentation/                             # plugins/presentation/skills/
    │   ├── .claude-plugin/
    │   │   └── plugin.json                       # Plugin manifest
    │   └── skills/
    │       ├── pptx-core-style/
    │       │   └── SKILL.md                      # Style guide for core architecture slides
    │       └── pptx-arch-style/
    │           └── SKILL.md                      # Style guide for architecture committee decks
    ├── obsidian/                                 # plugins/obsidian/skills/
    │   ├── .claude-plugin/
    │   │   └── plugin.json                       # Plugin manifest
    │   └── skills/
    │       └── offdesk/
    │           ├── SKILL.md                      # Skill definition and instructions
    │           └── references/
    │               └── setup.md                  # Syncthing + Obsidian Android manual setup
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
/plugin install presentation@dddpaul-claude-skills   # pptx-core-style + pptx-arch-style
/plugin install obsidian@dddpaul-claude-skills       # offdesk
/plugin install publish@dddpaul-claude-skills        # pdf + publish
```

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
