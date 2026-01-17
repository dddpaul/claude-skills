# Claude Code Skills

A collection of custom skills for Claude Code that extend its capabilities for architecture documentation and diagramming.

## Skills

### arch-describe

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

## Project Structure

```
claude-skills/
├── arch-describe/
│   ├── SKILL.md                    # Skill definition and instructions
│   └── references/
│       └── architectures.md        # Reference for 20+ common systems
├── arch-draw/
│   ├── SKILL.md                    # Skill definition and instructions
│   └── references/
│       ├── cheatsheet.md           # Quick reference for XML elements
│       └── agent-prompt.md         # Prompt templates and validation
└── README.md
```

## Installation

Add the skills directory to your Claude Code configuration:

```bash
# Add to your Claude Code settings
claude config add skills /path/to/claude-skills
```

Or configure in your project's `.claude/settings.json`:

```json
{
  "skills": ["/path/to/claude-skills"]
}
```

## Creating New Skills

Each skill follows this structure:

```
skill-name/
├── SKILL.md           # Required: Skill definition with frontmatter
└── references/        # Optional: Supporting documentation
    └── *.md
```

The `SKILL.md` file must include YAML frontmatter:

```yaml
---
name: skill-name
description: Brief description of when to use this skill
---
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
