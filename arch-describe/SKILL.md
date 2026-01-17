---
name: arch-describe
description: Generate detailed architectural descriptions of IT systems from short prompts. Produces structured output with overview, components list, connections/integrations, and ASCII diagrams with annotated arrows. Use when user asks to describe, explain, or document architecture of any IT system - specific platforms (Camunda, Kafka, Kubernetes), cloud services (AWS, GCP, Azure), databases, microservices, or custom systems.
---

# Architecture Describer

Generate structured IT architecture descriptions with ASCII diagrams.

## Output Structure

1. **Overview** - 2-3 sentences describing the system's purpose and high-level architecture
2. **Components** - Bulleted list of all components with brief descriptions
3. **Connections** - Numbered list of all integrations between components
4. **Diagram** - ASCII diagram showing components and annotated connections

## ASCII Diagram Conventions

Use box-drawing characters:

```
┌──────────────┐
│  Component   │
└──────────────┘
```

Arrow styles with annotations:

```
─────▶  unidirectional
◀────▶  bidirectional
──┬──   split/branch
──┴──   merge/join
```

Annotate arrows with protocol and purpose:

```
┌─────────┐   REST/get orders   ┌─────────┐
│ Service │────────────────────▶│   API   │
└─────────┘                     └─────────┘

┌─────────┐  gRPC/stream jobs   ┌─────────┐
│ Worker  │◀────────────────────│ Broker  │
└─────────┘                     └─────────┘
```

Vertical connections:

```
┌──────────┐
│  Source  │
└────┬─────┘
     │ JDBC/write
     ▼
┌──────────┐
│    DB    │
└──────────┘
```

## Example Output

**Prompt**: "Describe Camunda 8 architecture"

---

### Overview

Camunda 8 is a cloud-native process orchestration platform built on a distributed architecture. The core consists of Zeebe (workflow engine with brokers and gateway), operational tools (Operate, Tasklist, Optimize), and supporting infrastructure (Elasticsearch, Identity).

### Components

- **Zeebe Gateway** - Entry point for client applications, routes commands to brokers
- **Zeebe Broker Cluster** - Distributed workflow engine, processes BPMN workflows, manages state via Raft consensus
- **Elasticsearch** - Stores process data exported from brokers for querying
- **Operate** - Web UI for monitoring and troubleshooting process instances
- **Tasklist** - Web UI for human task management
- **Optimize** - Web UI for process analytics and reporting
- **Identity** - Authentication and authorization service (Keycloak-based)
- **Workers** - External applications that execute job tasks
- **Client Applications** - Applications that start process instances and interact with the platform

### Connections

1. Client Applications → Zeebe Gateway: gRPC/start process, create jobs
2. Zeebe Gateway → Zeebe Brokers: gRPC/route commands
3. Zeebe Brokers ↔ Zeebe Brokers: Raft/replication, leader election
4. Zeebe Brokers → Elasticsearch: HTTP/export process records
5. Workers ↔ Zeebe Gateway: gRPC/poll jobs, complete jobs
6. Operate → Elasticsearch: HTTP/query process data
7. Tasklist → Elasticsearch: HTTP/query tasks
8. Tasklist → Zeebe Gateway: gRPC/complete tasks
9. Optimize → Elasticsearch: HTTP/query analytics data
10. Identity → Operate, Tasklist, Optimize: OAuth2/authentication

### Diagram

```
┌───────────────────┐     gRPC/start process     ┌─────────────────┐
│ Client            │───────────────────────────▶│  Zeebe Gateway  │
│ Applications      │                            └────────┬────────┘
└───────────────────┘                                     │
                                                          │ gRPC/route
┌───────────────────┐     gRPC/poll & complete           ▼
│     Workers       │◀──────────────────────────▶┌─────────────────┐
└───────────────────┘                            │  Zeebe Broker   │
                                                 │    Cluster      │
                                                 │ ┌─────┬─────┐   │
                                                 │ │ B1 ◀─▶ B2 │   │
                                                 │ └──┬──┴──┬──┘   │
                                                 │    └──▶B3◀┘     │
                                                 │   Raft/replicate│
                                                 └────────┬────────┘
                                                          │
                                         HTTP/export      │
                                         records          ▼
┌───────────────┐                            ┌────────────────────┐
│   Identity    │──OAuth2/auth──────────────▶│   Elasticsearch    │
│  (Keycloak)   │                            └─────────┬──────────┘
└───────┬───────┘                                      │
        │                                              │ HTTP/query
        │ OAuth2/auth                                  ▼
        │                            ┌─────────────────────────────┐
        └───────────────────────────▶│  Operate  Tasklist  Optimize│
                                     └─────────────────────────────┘
```

---

## Common Architectures Reference

For common systems (Kafka, Kubernetes, Redis, etc.), see [references/architectures.md](references/architectures.md) for component lists and typical connection patterns.
