---
name: arch-draw
description: Generate professional draw.io diagrams in XML format from architectural descriptions. Use when Claude needs to create visual diagrams for (1) System architecture diagrams, (2) Microservices layouts, (3) Workflow/BPMN diagrams, (4) Network topology, (5) Data flow diagrams, (6) Any visual representation requiring boxes, containers, arrows, and connections. Handles arrow routing, collision avoidance, consistent layouts, and architectural patterns like three-tier, event-driven, and Camunda/Zeebe clusters.
---

# Draw.io Diagram Generation Skill

## Overview

This skill enables AI agents to generate professional, clean draw.io diagrams in XML format. It addresses common challenges including arrow routing, collision avoidance, consistent layouts, and architectural pattern representation.

## Quick Reference

- **Cheatsheet**: See [references/cheatsheet.md](references/cheatsheet.md) for copy-paste XML snippets, color codes, and common element templates
- **Agent Prompts**: See [references/agent-prompt.md](references/agent-prompt.md) for system/user prompt templates and validation checklist

## File Format Basics

Draw.io uses mxGraph XML format. Basic structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="AI-Agent" version="22.0.0" type="device">
  <diagram id="unique-id" name="Diagram Name">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- All elements go here with parent="1" -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Grid System and Spacing

### Core Principles

1. **Always use 10px grid alignment** — All coordinates should be multiples of 10
2. **Minimum spacing between elements**: 40px horizontal, 30px vertical
3. **Standard element sizes**:
   - Small boxes: 100x50
   - Medium boxes: 120x60
   - Large containers: 150-200 width, height as needed
   - Swimlanes: 140-180 width

### Layout Zones

Divide canvas into logical zones (left-to-right flow example):

```
| Zone 1      | Zone 2           | Zone 3        |
| x: 40-180   | x: 240-760       | x: 820-960    |
| Producers/  | Processing/      | Consumers/    |
| Inputs      | Core System      | Outputs       |
```

## Element Creation

### Basic Shape

```xml
<mxCell id="unique-id" value="Label Text" 
  style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;" 
  parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

### Container/Swimlane

```xml
<mxCell id="container-1" value="Container Title" 
  style="swimlane;horizontal=1;startSize=30;fillColor=#f5f5f5;strokeColor=#666666;rounded=1;fontSize=14;fontStyle=1;" 
  parent="1" vertex="1">
  <mxGeometry x="40" y="80" width="200" height="300" as="geometry"/>
</mxCell>

<!-- Child elements use container as parent -->
<mxCell id="child-1" value="Child Element" 
  style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" 
  parent="container-1" vertex="1">
  <mxGeometry x="20" y="50" width="160" height="50" as="geometry"/>
</mxCell>
```

**Important**: Child geometry is RELATIVE to parent container origin.

### Grouped Elements

For logical grouping without visual container:

```xml
<mxCell id="group-1" value="" style="group" parent="1" vertex="1" connectable="0">
  <mxGeometry x="100" y="100" width="200" height="150" as="geometry"/>
</mxCell>
<!-- Children reference group-1 as parent -->
```

## Arrow Routing — Critical Section

### Problem Statement

Arrow collisions and messy routing are the #1 issue in generated diagrams. Follow these rules strictly.

### Connection Points

Use explicit entry/exit points on shapes (values 0-1 represent percentage):

```xml
<mxCell id="arrow-1" value="" 
  style="endArrow=classic;html=1;strokeWidth=2;strokeColor=#6c8ebf;
         exitX=1;exitY=0.5;exitDx=0;exitDy=0;
         entryX=0;entryY=0.5;entryDx=0;entryDy=0;" 
  parent="1" source="box-1" target="box-2" edge="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Connection Point Reference

```
        entryX=0.5;entryY=0 (top center)
                    |
entryX=0  +---------+---------+  entryX=1
entryY=0.5|                   |  entryY=0.5
(left)    |      SHAPE        |  (right)
          |                   |
          +---------+---------+
                    |
        entryX=0.5;entryY=1 (bottom center)
```

### Arrow Routing Strategies

#### Strategy 1: Horizontal Flow (Left-to-Right)

For standard architecture diagrams:

```
Source (exitX=1, exitY=0.5) ----→ Target (entryX=0, entryY=0.5)
```

#### Strategy 2: Vertical Stagger

When multiple arrows go to same target, stagger entry points:

```xml
<!-- Arrow 1: enters at top-left area -->
<mxCell style="...entryX=0;entryY=0.25;..." />

<!-- Arrow 2: enters at middle-left -->
<mxCell style="...entryX=0;entryY=0.5;..." />

<!-- Arrow 3: enters at bottom-left area -->
<mxCell style="...entryX=0;entryY=0.75;..." />
```

#### Strategy 3: Waypoints for Complex Routes

Use explicit waypoints to avoid collisions:

```xml
<mxCell id="routed-arrow" style="endArrow=classic;html=1;rounded=1;strokeWidth=2;" 
  parent="1" source="A" target="B" edge="1">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="300" y="150"/>
      <mxPoint x="300" y="250"/>
    </Array>
  </mxGeometry>
</mxCell>
```

#### Strategy 4: Orthogonal Routing

For clean right-angle paths:

```xml
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
```

#### Strategy 5: Curved Routing

For avoiding obstacles elegantly:

```xml
style="edgeStyle=orthogonalEdgeStyle;rounded=1;curved=1;..."
```

### Arrow Collision Avoidance Rules

1. **Never cross through shapes** — Route around using waypoints
2. **Minimum 20px spacing between parallel arrows**
3. **Use different Y-levels for arrows going same direction**:
   ```
   Arrow 1: y=100 →→→→→→→→→→
   Arrow 2: y=130 →→→→→→→→→→
   Arrow 3: y=160 →→→→→→→→→→
   ```
4. **Bidirectional connections**: Use slight Y offset or curved style
5. **For many-to-one**: Fan pattern with staggered entry points

### Arrow Style Reference

```xml
<!-- Solid arrow -->
style="endArrow=classic;html=1;strokeWidth=2;strokeColor=#333333;"

<!-- Dashed arrow (async, optional) -->
style="endArrow=classic;html=1;dashed=1;strokeColor=#666666;"

<!-- Bidirectional -->
style="endArrow=classic;startArrow=classic;html=1;"

<!-- No arrow (line only) -->
style="endArrow=none;html=1;"

<!-- Open arrow head -->
style="endArrow=open;html=1;"

<!-- Diamond (composition) -->
style="endArrow=diamond;endFill=1;html=1;"

<!-- Diamond hollow (aggregation) -->
style="endArrow=diamond;endFill=0;html=1;"
```

## Color Schemes

### Recommended Palettes

#### Enterprise/Professional

| Purpose | Fill | Stroke | Usage |
|---------|------|--------|-------|
| Primary | #dae8fc | #6c8ebf | Main components |
| Secondary | #d5e8d4 | #82b366 | Services, success |
| Accent | #fff2cc | #d6b656 | Inputs, triggers |
| Warning | #f8cecc | #b85450 | Errors, replicas |
| Neutral | #f5f5f5 | #666666 | Containers, background |
| Purple | #e1d5e7 | #9673a6 | Data, storage |
| Orange | #ffe6cc | #d79b00 | External systems |

#### Workflow/Process (Camunda-style)

| Purpose | Fill | Stroke | Usage |
|---------|------|--------|-------|
| Start Event | #d5e8d4 | #82b366 | Circle, green |
| End Event | #f8cecc | #b85450 | Circle, red |
| Task | #dae8fc | #6c8ebf | Rounded rectangle |
| Gateway | #fff2cc | #d6b656 | Diamond |
| Subprocess | #e1d5e7 | #9673a6 | Rounded, dashed |
| Message | #ffe6cc | #d79b00 | Communication |

### Applying Colors

```xml
style="...fillColor=#dae8fc;strokeColor=#6c8ebf;fontColor=#333333;..."
```

## Common Architectural Patterns

### Pattern 1: Three-Tier Architecture

```
[Clients]  →  [Load Balancer]  →  [App Servers]  →  [Database]
   x:40          x:200              x:400            x:600
```

Layout: 4 columns, 160px spacing, centered vertically.

### Pattern 2: Microservices

```
         [API Gateway]
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
[Svc A]   [Svc B]   [Svc C]
    ↓         ↓         ↓
    └─────────┼─────────┘
              ↓
        [Message Bus]
              ↓
    ┌─────────┼─────────┐
[DB A]    [DB B]    [DB C]
```

Layout: Central spine at x=400, services spread ±200px.

### Pattern 3: Event-Driven / Kafka

```
[Producers] → [Kafka Cluster] → [Consumers]
                   ↕
              [ZK/KRaft]
```

Layout: Producers left, cluster center (wide), consumers right, coordination below.

### Pattern 4: Workflow/BPMN Style

```
(Start) → [Task 1] → <Gateway> → [Task 2a] → (End)
                         ↓
                    [Task 2b] ↗
```

Layout: Horizontal swimlane, 120px between elements, gateways as decision points.

## Camunda 8 Specific Patterns

### Zeebe Cluster Layout

```
┌─────────────────────────────────────────────┐
│              Zeebe Cluster                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │Broker 0 │ │Broker 1 │ │Broker 2 │       │
│  │(Raft)   │ │(Raft)   │ │(Raft)   │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│        ↕           ↕           ↕            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │Gateway 0│ │Gateway 1│ │Gateway 2│       │
│  └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────┘
          ↑                     ↓
    [Job Workers]         [Operate/Tasklist]
```

### Process Instance Flow

Use BPMN-like symbols:
- Start: Circle with thin border
- End: Circle with thick border  
- Task: Rounded rectangle with icon
- Gateway: Diamond (45° rotated square)
- Event: Circle with appropriate icon

## Text and Labels

### Font Styles

```xml
<!-- Title -->
style="text;fontSize=20;fontStyle=1;fontColor=#333333;"

<!-- Label -->
style="text;fontSize=12;fontColor=#666666;"

<!-- Code/Technical -->
style="text;fontSize=11;fontFamily=Courier New;fontColor=#333333;"
```

### Multi-line Text

Use `&#xa;` for line breaks in values:

```xml
value="Line 1&#xa;Line 2&#xa;Line 3"
```

### Label Positioning on Arrows

```xml
<mxCell id="arrow" style="edgeStyle=orthogonalEdgeStyle;..." edge="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
<!-- Separate label cell -->
<mxCell id="arrow-label" value="Label" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;" 
  parent="arrow" vertex="1" connectable="0">
  <mxGeometry x="0.5" relative="1" as="geometry">
    <mxPoint x="-20" y="-10" as="offset"/>
  </mxGeometry>
</mxCell>
```

## Complete Example: Microservice Architecture

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram id="microservices" name="Microservices">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        
        <!-- API Gateway -->
        <mxCell id="gateway" value="API Gateway" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=12;fontStyle=1;" parent="1" vertex="1">
          <mxGeometry x="340" y="40" width="120" height="50" as="geometry"/>
        </mxCell>
        
        <!-- Services Row -->
        <mxCell id="svc-a" value="Service A&#xa;(Users)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;" parent="1" vertex="1">
          <mxGeometry x="140" y="140" width="100" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="svc-b" value="Service B&#xa;(Orders)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;" parent="1" vertex="1">
          <mxGeometry x="350" y="140" width="100" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="svc-c" value="Service C&#xa;(Inventory)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;" parent="1" vertex="1">
          <mxGeometry x="560" y="140" width="100" height="60" as="geometry"/>
        </mxCell>
        
        <!-- Message Bus -->
        <mxCell id="bus" value="Message Bus (Kafka)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;fontStyle=1;" parent="1" vertex="1">
          <mxGeometry x="240" y="260" width="320" height="40" as="geometry"/>
        </mxCell>
        
        <!-- Databases -->
        <mxCell id="db-a" value="Users DB" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" parent="1" vertex="1">
          <mxGeometry x="155" y="350" width="70" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="db-b" value="Orders DB" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" parent="1" vertex="1">
          <mxGeometry x="365" y="350" width="70" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="db-c" value="Inventory DB" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" parent="1" vertex="1">
          <mxGeometry x="575" y="350" width="70" height="60" as="geometry"/>
        </mxCell>
        
        <!-- Arrows: Gateway to Services -->
        <mxCell id="gw-a" style="endArrow=classic;html=1;strokeWidth=2;strokeColor=#d79b00;exitX=0;exitY=1;entryX=0.5;entryY=0;" parent="1" source="gateway" target="svc-a" edge="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="gw-b" style="endArrow=classic;html=1;strokeWidth=2;strokeColor=#d79b00;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" parent="1" source="gateway" target="svc-b" edge="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="gw-c" style="endArrow=classic;html=1;strokeWidth=2;strokeColor=#d79b00;exitX=1;exitY=1;entryX=0.5;entryY=0;" parent="1" source="gateway" target="svc-c" edge="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        
        <!-- Arrows: Services to Bus (staggered entry) -->
        <mxCell id="a-bus" style="endArrow=classic;startArrow=classic;html=1;strokeWidth=1;strokeColor=#82b366;exitX=0.5;exitY=1;entryX=0.15;entryY=0;" parent="1" source="svc-a" target="bus" edge="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="b-bus" style="endArrow=classic;startArrow=classic;html=1;strokeWidth=1;strokeColor=#82b366;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" parent="1" source="svc-b" target="bus" edge="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="c-bus" style="endArrow=classic;startArrow=classic;html=1;strokeWidth=1;strokeColor=#82b366;exitX=0.5;exitY=1;entryX=0.85;entryY=0;" parent="1" source="svc-c" target="bus" edge="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        
        <!-- Arrows: Services to DBs -->
        <mxCell id="a-db" style="endArrow=classic;startArrow=classic;html=1;strokeWidth=1;dashed=1;strokeColor=#9673a6;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" parent="1" source="svc-a" target="db-a" edge="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="190" y="330"/>
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="b-db" style="endArrow=classic;startArrow=classic;html=1;strokeWidth=1;dashed=1;strokeColor=#9673a6;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" parent="1" source="svc-b" target="db-b" edge="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="400" y="330"/>
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="c-db" style="endArrow=classic;startArrow=classic;html=1;strokeWidth=1;dashed=1;strokeColor=#9673a6;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" parent="1" source="svc-c" target="db-c" edge="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="610" y="330"/>
            </Array>
          </mxGeometry>
        </mxCell>
        
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Checklist Before Output

1. ✅ All coordinates are multiples of 10
2. ✅ Minimum 40px horizontal spacing between elements
3. ✅ All arrows have explicit entry/exit points
4. ✅ No arrow crosses through shapes
5. ✅ Parallel arrows have different Y-levels or staggered connection points
6. ✅ Consistent color scheme throughout
7. ✅ All IDs are unique
8. ✅ Child elements have correct parent reference
9. ✅ Child geometry is relative to parent
10. ✅ Labels are readable (fontSize ≥ 10)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Arrows crossing shapes | Add waypoints to route around |
| Arrows overlapping | Stagger entry/exit Y values |
| Elements misaligned | Ensure coordinates are ×10 |
| Child elements in wrong position | Check parent reference, use relative coords |
| Text cut off | Increase element width or use `whiteSpace=wrap` |
| Colors inconsistent | Use defined palette variables |
| Diagram too cramped | Increase canvas size in mxGraphModel |

## Integration Notes

For AI agent integration:

1. **Input**: Accept natural language description or structured schema
2. **Planning**: Determine layout pattern, count elements, calculate spacing
3. **Generation**: Build XML following this skill's rules
4. **Validation**: Check against the checklist above
5. **Output**: Complete `.drawio` XML file

When generating programmatically, consider:
- Pre-calculating all positions before generating XML
- Building a coordinate map to check for collisions
- Using consistent ID naming scheme (e.g., `{type}-{index}`)
