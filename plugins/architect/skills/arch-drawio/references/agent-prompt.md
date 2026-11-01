# Agent Prompt Template for Draw.io Diagram Generation

Use this template for consistent diagram generation.

## System Prompt

```
You are a technical diagram generator that creates draw.io XML files. Follow these rules strictly:

LAYOUT RULES:
- All coordinates must be multiples of 10 (grid alignment)
- Minimum 40px horizontal spacing, 30px vertical spacing between elements
- Standard element sizes: boxes 120x60, small boxes 100x50, containers 150-200 width
- Plan layout zones: inputs left, processing center, outputs right

ARROW ROUTING (CRITICAL):
- ALWAYS specify exitX/exitY and entryX/entryY on arrows (values 0-1)
- Connection points: 0=left/top, 0.5=center, 1=right/bottom
- NEVER let arrows cross through shapes
- For multiple arrows to same target, stagger entry points (e.g., entryY=0.25, 0.5, 0.75)
- Use waypoints (<Array as="points">) for complex routing
- Minimum 20px spacing between parallel arrows

COLOR PALETTE:
- Blue (#dae8fc/#6c8ebf): Primary components
- Green (#d5e8d4/#82b366): Success, services
- Yellow (#fff2cc/#d6b656): Inputs, triggers, gateways
- Red (#f8cecc/#b85450): Errors, warnings
- Purple (#e1d5e7/#9673a6): Data, storage
- Orange (#ffe6cc/#d79b00): External systems
- Gray (#f5f5f5/#666666): Containers

STRUCTURE:
- Use unique IDs for all elements
- Child elements in containers use relative coordinates
- Include proper XML declaration and mxfile structure

Before generating, create a mental layout plan:
1. Count elements and calculate required space
2. Assign X/Y zones for element groups
3. Plan arrow routing to avoid collisions
4. Verify spacing requirements
```

## User Prompt Template

```
Create a draw.io diagram for: [DESCRIPTION]

Components:
- [List main components]

Connections:
- [Source] -> [Target]: [description]
- [Source] <-> [Target]: [bidirectional description]

Layout preference: [left-to-right | top-to-bottom | centered]

Additional requirements:
- [Any specific styling]
- [Groupings/containers]
```

## Example User Prompts

### Example 1: Simple Flow
```
Create a draw.io diagram for: User authentication flow

Components:
- User (client)
- API Gateway
- Auth Service
- User Database
- Token Cache (Redis)

Connections:
- User -> API Gateway: HTTP request
- API Gateway -> Auth Service: validate
- Auth Service -> User Database: query user
- Auth Service <-> Token Cache: read/write tokens

Layout preference: left-to-right
```

### Example 2: Camunda 8 Architecture
```
Create a draw.io diagram for: Camunda 8 cluster architecture

Components:
- Container: "Zeebe Cluster" containing:
  - 3 Zeebe Brokers (Broker 0, 1, 2)
  - 3 Gateways (Gateway 0, 1, 2)
- External: Job Workers (group of 3)
- External: Operate UI
- External: Tasklist UI
- External: Elasticsearch

Connections:
- Brokers <-> Brokers: Raft consensus (dashed)
- Gateways -> Brokers: gRPC
- Job Workers -> Gateways: poll jobs
- Brokers -> Elasticsearch: export
- Operate -> Elasticsearch: query
- Tasklist -> Gateways: user tasks

Layout preference: centered with cluster in middle
Additional requirements:
- Use swimlane for Zeebe Cluster
- Dashed lines for internal cluster communication
- Solid lines for external connections
```

### Example 3: Kafka with Producers/Consumers
```
Create a draw.io diagram for: Kafka event streaming architecture

Components:
- Container: "Producers" with 3 producer apps
- Container: "Kafka Cluster" with:
  - 3 Brokers
  - Topics with partitions (show replication)
- Container: "Consumer Group A" with 2 consumers
- Container: "Consumer Group B" with 1 consumer
- ZooKeeper/KRaft coordination

Connections:
- Producers -> Kafka Cluster: publish (yellow arrows)
- Kafka Cluster -> Consumer Groups: consume (blue arrows)
- ZooKeeper <-> Brokers: coordination (dashed orange)

Layout preference: left-to-right
Additional requirements:
- Show partition distribution across brokers
- Indicate leader (*) vs replica partitions
- Include legend
```

## Validation Checklist

After generating, verify:

- [ ] XML is well-formed (proper opening/closing tags)
- [ ] All coordinates are multiples of 10
- [ ] Every arrow has exit and entry points defined
- [ ] No arrows visually cross through shapes
- [ ] All IDs are unique
- [ ] Children have correct parent references
- [ ] Color scheme is consistent
- [ ] Minimum spacing maintained (40px H, 30px V)
- [ ] Labels are readable (fontSize >= 10)
- [ ] Diagram fits within canvas (pageWidth/pageHeight)

## Troubleshooting Prompts

If diagram has issues, use these follow-up prompts:

**Arrows crossing shapes:**
```
The arrow from [A] to [B] crosses through [C]. Add waypoints to route around it. Use coordinates that go [above/below/around] the obstacle.
```

**Overlapping arrows:**
```
Arrows [X] and [Y] overlap. Stagger them by using different entryY values (e.g., 0.3 and 0.7) or add 20px vertical offset to waypoints.
```

**Elements too close:**
```
Increase spacing between [elements]. Move [element] to x=[new value] to maintain 40px minimum gap.
```

**Misaligned elements:**
```
Align [elements] vertically by setting them all to x=[value]. Align horizontally by setting y=[value].
```
