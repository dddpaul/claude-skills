# Draw.io Quick Reference Cheatsheet

## Minimal Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram id="id" name="Name">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- elements here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Elements

### Rectangle
```xml
<mxCell id="box1" value="Label" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

### Circle
```xml
<mxCell id="circle1" value="" style="ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="50" height="50" as="geometry"/>
</mxCell>
```

### Diamond (Gateway)
```xml
<mxCell id="gw1" value="" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="50" height="50" as="geometry"/>
</mxCell>
```

### Cylinder (Database)
```xml
<mxCell id="db1" value="DB" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#e1d5e7;strokeColor=#9673a6;" parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="60" height="80" as="geometry"/>
</mxCell>
```

### Container/Swimlane
```xml
<mxCell id="container1" value="Title" style="swimlane;horizontal=1;startSize=30;fillColor=#f5f5f5;strokeColor=#666666;rounded=1;" parent="1" vertex="1">
  <mxGeometry x="40" y="40" width="200" height="300" as="geometry"/>
</mxCell>
<!-- Children use parent="container1" with RELATIVE coordinates -->
```

### Text Label
```xml
<mxCell id="label1" value="Text" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=12;" parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="80" height="20" as="geometry"/>
</mxCell>
```

## Arrows

### Basic Arrow
```xml
<mxCell id="arrow1" style="endArrow=classic;html=1;strokeWidth=2;" parent="1" source="box1" target="box2" edge="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Arrow with Entry/Exit Points
```xml
<mxCell id="arrow2" style="endArrow=classic;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" parent="1" source="box1" target="box2" edge="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Arrow with Waypoints
```xml
<mxCell id="arrow3" style="endArrow=classic;html=1;rounded=1;" parent="1" source="box1" target="box2" edge="1">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="200" y="150"/>
      <mxPoint x="200" y="250"/>
    </Array>
  </mxGeometry>
</mxCell>
```

### Orthogonal (Right-Angle) Routing
```xml
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
```

## Connection Points Map

```
      (0.5, 0) TOP
          |
(0,0.5)---+---(1,0.5)
LEFT      |      RIGHT
          |
     (0.5, 1) BOTTOM
```

Values: `exitX`, `exitY`, `entryX`, `entryY` (0 to 1)

## Arrow Styles

| Style | Code |
|-------|------|
| Solid | `strokeWidth=2;` |
| Dashed | `dashed=1;` |
| Bidirectional | `endArrow=classic;startArrow=classic;` |
| No arrow | `endArrow=none;` |
| Open head | `endArrow=open;` |
| Diamond filled | `endArrow=diamond;endFill=1;` |
| Diamond hollow | `endArrow=diamond;endFill=0;` |

## Color Palette

| Name | Fill | Stroke |
|------|------|--------|
| Blue | #dae8fc | #6c8ebf |
| Green | #d5e8d4 | #82b366 |
| Yellow | #fff2cc | #d6b656 |
| Red | #f8cecc | #b85450 |
| Gray | #f5f5f5 | #666666 |
| Purple | #e1d5e7 | #9673a6 |
| Orange | #ffe6cc | #d79b00 |

## Font Styles

```xml
fontSize=12;fontStyle=0;  /* Normal */
fontSize=14;fontStyle=1;  /* Bold */
fontSize=12;fontStyle=2;  /* Italic */
fontSize=12;fontStyle=3;  /* Bold+Italic */
fontColor=#333333;
fontFamily=Helvetica;
```

## Multi-line Text

Use `&#xa;` for newlines:
```xml
value="Line 1&#xa;Line 2&#xa;Line 3"
```

## Spacing Rules

- Grid: 10px
- Min horizontal gap: 40px
- Min vertical gap: 30px
- Standard box: 120x60
- Small box: 100x50
- Swimlane width: 140-180

## Common Mistakes

| Wrong | Correct |
|-------|---------|
| `x="115"` | `x="120"` (use grid x10) |
| Child with absolute coords | Child coords relative to parent |
| Arrows without entry/exit | Always specify connection points |
| `parent="0"` | `parent="1"` (or container ID) |
