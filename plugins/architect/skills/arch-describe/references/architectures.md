# Common Architecture Patterns

Quick reference for frequently used systems. Use as a starting point - adapt based on specific deployment context.

## Table of Contents

- [Apache Kafka](#apache-kafka)
- [Kubernetes](#kubernetes)
- [PostgreSQL HA](#postgresql-ha)
- [MongoDB Replica Set](#mongodb-replica-set)
- [Redis Cluster](#redis-cluster)
- [Elasticsearch](#elasticsearch)
- [Keycloak](#keycloak)
- [MinIO](#minio)
- [ClickHouse](#clickhouse)
- [Temporal](#temporal)
- [Apache Flink](#apache-flink)
- [Apache Airflow](#apache-airflow)
- [Debezium](#debezium)
- [Microservices Pattern](#microservices-pattern)
- [HashiCorp Vault](#hashicorp-vault)
- [Apache Cassandra](#apache-cassandra)
- [Neo4j](#neo4j)
- [Qdrant](#qdrant)
- [Envoy / Istio](#envoy--istio)
- [ArgoCD](#argocd)
- [OpenTelemetry](#opentelemetry)
- [Apache Spark](#apache-spark)
- [Apache Iceberg / Parquet](#apache-iceberg--parquet)
- [HDFS](#hdfs)

---

## Apache Kafka

**Components:**
- Kafka Brokers - Message storage and replication
- ZooKeeper/KRaft - Cluster coordination (KRaft replaces ZK in newer versions)
- Schema Registry - Avro/Protobuf schema management
- Kafka Connect - Source/sink connectors for external systems
- Producers - Applications publishing messages
- Consumers - Applications consuming messages
- Consumer Groups - Coordinated consumer instances

**Key Connections:**
- Producers → Brokers: TCP/publish messages
- Brokers ↔ Brokers: TCP/replication
- Consumers → Brokers: TCP/fetch messages
- Brokers → ZooKeeper: TCP/metadata, leader election
- Connect → Brokers: TCP/produce/consume
- Connect → External Systems: varies/source/sink data
- Clients → Schema Registry: HTTP/schema lookup

---

## Kubernetes

**Components:**
- API Server - Cluster entry point, REST API
- etcd - Distributed key-value store for cluster state
- Controller Manager - Runs controllers (deployment, replicaset, etc.)
- Scheduler - Assigns pods to nodes
- kubelet - Node agent, manages containers
- kube-proxy - Network proxy on each node
- CoreDNS - Cluster DNS service
- Ingress Controller - External traffic routing
- Container Runtime - containerd/CRI-O

**Key Connections:**
- kubectl → API Server: HTTPS/cluster operations
- API Server → etcd: gRPC/read/write state
- Controller Manager → API Server: HTTPS/watch resources
- Scheduler → API Server: HTTPS/watch pods, bind to nodes
- kubelet → API Server: HTTPS/report status, get pod specs
- kubelet → Container Runtime: CRI/manage containers
- kube-proxy → API Server: HTTPS/watch services
- Ingress Controller → API Server: HTTPS/watch ingress rules
- Pods → CoreDNS: DNS/service discovery

---

## PostgreSQL HA

**Components:**
- Primary - Read/write database instance
- Replicas - Read-only standby instances
- Patroni/Stolon - HA management and failover
- etcd/Consul/ZK - Distributed consensus for leader election
- PgBouncer - Connection pooling
- WAL-G/pgBackRest - Backup management
- Applications - Database clients

**Key Connections:**
- Applications → PgBouncer: TCP/5432/queries
- PgBouncer → Primary: TCP/5432/read-write queries
- PgBouncer → Replicas: TCP/5432/read queries
- Primary → Replicas: TCP/streaming replication (WAL)
- Patroni → etcd: HTTP/leader election, config
- Patroni → PostgreSQL: local/manage instance
- WAL-G → Object Storage: HTTPS/backup WAL segments

---

## MongoDB Replica Set

**Components:**
- Primary - Accepts writes
- Secondaries - Replicate from primary, serve reads
- Arbiter - Votes in elections, no data
- mongos - Query router (sharded clusters)
- Config Servers - Metadata for sharding
- Applications - MongoDB clients

**Key Connections:**
- Applications → Primary: TCP/27017/write operations
- Applications → Secondaries: TCP/27017/read operations (read preference)
- Primary → Secondaries: TCP/oplog replication
- Replica members ↔ Replica members: TCP/heartbeat, election
- mongos → Config Servers: TCP/routing metadata
- mongos → Shards: TCP/query routing

---

## Redis Cluster

**Components:**
- Redis Nodes - Data partitioned via hash slots (16384 slots)
- Master Nodes - Handle read/write for assigned slots
- Replica Nodes - Replicate masters, failover candidates
- Redis Sentinel - HA monitoring (non-cluster mode)
- Applications - Redis clients

**Key Connections:**
- Applications → Masters: TCP/6379/read-write
- Applications → Replicas: TCP/6379/read (READONLY mode)
- Masters → Replicas: TCP/replication stream
- Nodes ↔ Nodes: TCP/gossip protocol (cluster bus port +10000)
- Sentinel → Redis Nodes: TCP/monitoring, failover coordination

---

## Elasticsearch

**Components:**
- Master Nodes - Cluster management, index metadata
- Data Nodes - Store shards, execute queries
- Coordinating Nodes - Route requests, aggregate results
- Ingest Nodes - Pre-process documents (pipelines)
- Kibana - Visualization and management UI
- Logstash/Beats - Data ingestion
- Applications - Search clients

**Key Connections:**
- Applications → Coordinating Nodes: HTTP/9200/search, index
- Coordinating → Data Nodes: TCP/9300/shard queries
- Data Nodes ↔ Data Nodes: TCP/9300/shard replication
- Master ↔ All Nodes: TCP/9300/cluster state
- Kibana → Elasticsearch: HTTP/9200/queries, management
- Logstash → Elasticsearch: HTTP/9200/bulk index
- Beats → Elasticsearch: HTTP/9200/index events

---

## Keycloak

**Components:**
- Keycloak Server - Identity and access management
- Database - PostgreSQL/MySQL for persistence
- Infinispan Cache - Distributed caching (embedded or external)
- LDAP/AD - External user federation
- Applications - Protected services
- Identity Providers - External IdPs (Google, SAML, etc.)

**Key Connections:**
- Applications → Keycloak: HTTP/OAuth2, OIDC/authenticate, get tokens
- Keycloak → Database: JDBC/store users, realms, clients
- Keycloak ↔ Keycloak: Infinispan/session replication (clustered)
- Keycloak → LDAP: LDAP/389,636/user federation
- Keycloak → External IdPs: HTTP/SAML, OIDC/federated login
- Applications → Keycloak: HTTP/token validation, user info

---

## MinIO

**Components:**
- MinIO Server Nodes - Object storage (distributed mode)
- Load Balancer - Distributes requests across nodes
- MinIO Console - Web-based management UI
- mc CLI - Command-line client
- Applications - S3-compatible clients
- Bucket Notifications - Event destinations (Kafka, webhook, etc.)

**Key Connections:**
- Applications → Load Balancer: HTTPS/S3 API
- Load Balancer → MinIO Nodes: HTTP/9000/distribute requests
- MinIO Nodes ↔ MinIO Nodes: HTTP/erasure coding, replication
- Console → MinIO: HTTP/9001/management API
- MinIO → Kafka/Webhook: HTTP, TCP/bucket event notifications
- mc → MinIO: HTTP/S3 API/admin operations

---

## ClickHouse

**Components:**
- ClickHouse Server Nodes - Column-oriented OLAP database
- ZooKeeper/ClickHouse Keeper - Coordination for replication
- Shards - Horizontal data partitioning
- Replicas - Data redundancy within shards
- ClickHouse Proxy - Load balancing, connection pooling
- Applications - Analytics clients

**Key Connections:**
- Applications → ClickHouse: HTTP/8123, TCP/9000/queries
- Applications → Proxy: TCP/load-balanced queries
- ClickHouse → ZooKeeper: TCP/2181/replication coordination
- Replicas ↔ Replicas: TCP/9009/data replication
- Distributed tables → Shards: TCP/9000/distributed queries

---

## Temporal

**Components:**
- Temporal Server (Frontend) - Client API gateway
- History Service - Workflow state management
- Matching Service - Task queue management
- Worker Service - Internal background tasks
- Persistence (Cassandra/PostgreSQL/MySQL) - Workflow state storage
- Elasticsearch - Visibility and search
- Workers - Execute workflow/activity code
- Temporal Web UI - Workflow monitoring

**Key Connections:**
- Workers → Frontend: gRPC/poll tasks, complete tasks
- Client Applications → Frontend: gRPC/start workflows, signals
- Frontend → History: gRPC/workflow operations
- Frontend → Matching: gRPC/task queue operations
- History → Persistence: SQL, CQL/workflow state
- History → Elasticsearch: HTTP/visibility records
- Web UI → Frontend: gRPC-Web/workflow queries

---

## Apache Flink

**Components:**
- JobManager - Coordinates distributed execution
- TaskManagers - Execute stream/batch operators
- ResourceManager - Manages TaskManager slots
- Dispatcher - REST API, job submission
- ZooKeeper - HA for JobManager (leader election)
- State Backend - RocksDB/heap for checkpoints
- Checkpoint Storage - HDFS/S3 for checkpoint data
- Kafka/Kinesis - Stream sources/sinks

**Key Connections:**
- Client → Dispatcher: REST/submit jobs
- Dispatcher → JobManager: RPC/job coordination
- JobManager → TaskManagers: RPC/deploy tasks, checkpoints
- TaskManagers ↔ TaskManagers: TCP/data shuffle
- JobManager → ZooKeeper: TCP/leader election, metadata
- TaskManagers → State Backend: local/state operations
- JobManager → Checkpoint Storage: HDFS, S3/checkpoint persistence
- TaskManagers → Kafka: TCP/consume, produce streams

---

## Apache Airflow

**Components:**
- Web Server - UI and REST API
- Scheduler - Triggers DAG runs, schedules tasks
- Executor - Runs tasks (Local, Celery, Kubernetes)
- Workers - Execute task instances (Celery/K8s pods)
- Metadata Database - PostgreSQL/MySQL for DAG state
- Redis/RabbitMQ - Message broker (Celery executor)
- DAG Files - Python DAG definitions
- Triggerer - Handles deferrable operators

**Key Connections:**
- Users → Web Server: HTTP/8080/UI, API
- Web Server → Metadata DB: SQL/read DAG state
- Scheduler → Metadata DB: SQL/read DAGs, write task states
- Scheduler → Executor: internal/submit tasks
- Executor → Redis: TCP/6379/task queue (Celery)
- Workers → Redis: TCP/6379/fetch tasks
- Workers → Metadata DB: SQL/update task status
- Scheduler → DAG Files: filesystem/parse DAGs

---

## Debezium

**Components:**
- Debezium Connectors - Capture changes from databases
- Kafka Connect - Hosts Debezium connectors
- Kafka - Streams change events
- Source Database - PostgreSQL, MySQL, MongoDB, etc.
- Schema Registry - Manages Avro schemas
- Consumers - Applications processing CDC events

**Key Connections:**
- Debezium → Source DB: TCP/read WAL, binlog, oplog
- Debezium → Kafka: TCP/publish change events
- Debezium → Schema Registry: HTTP/register schemas
- Kafka Connect → Kafka: TCP/connector coordination
- Consumers → Kafka: TCP/consume CDC events
- Consumers → Schema Registry: HTTP/fetch schemas

---

## Microservices Pattern

**Components:**
- API Gateway - Entry point, routing, auth
- Service Mesh (Istio/Linkerd) - Service-to-service communication
- Service Discovery (Consul/etcd) - Service registry
- Config Server - Centralized configuration
- Message Broker (Kafka/RabbitMQ) - Async communication
- Distributed Cache (Redis) - Shared caching
- Databases - Service-specific data stores
- Observability Stack - Prometheus, Grafana, Jaeger
- Services - Individual microservices

**Key Connections:**
- Clients → API Gateway: HTTPS/API requests
- API Gateway → Services: HTTP, gRPC/route requests
- Services → Service Discovery: HTTP/register, discover
- Services ↔ Services: HTTP, gRPC/sync calls (via mesh)
- Services → Message Broker: TCP/async events
- Services → Config Server: HTTP/fetch config
- Services → Cache: TCP/6379/cache operations
- Services → Databases: TCP/data persistence
- Services → Observability: HTTP/metrics, traces

---

## HashiCorp Vault

**Components:**
- Vault Server - Secrets management, encryption as a service
- Storage Backend - Consul, etcd, Raft (integrated), or filesystem
- Seal/Unseal Mechanism - Auto-unseal (AWS KMS, Azure, GCP) or Shamir keys
- Auth Methods - LDAP, OIDC, Kubernetes, AppRole, tokens
- Secrets Engines - KV, PKI, database credentials, AWS/GCP/Azure dynamic secrets
- Audit Devices - Log all requests (file, syslog, socket)
- Vault Agent - Sidecar for auto-auth and secret caching
- Vault UI - Web interface for management

**Key Connections:**
- Applications → Vault: HTTPS/8200/read secrets, encrypt data
- Vault Agent → Vault: HTTPS/auto-auth, cache secrets
- Vault → Storage Backend: TCP/persist encrypted data
- Vault → Auth Backend (LDAP/OIDC): LDAP, HTTPS/authenticate users
- Vault → Cloud KMS: HTTPS/auto-unseal keys
- Vault → Databases: TCP/rotate credentials, generate dynamic secrets
- Vault → Kubernetes API: HTTPS/service account auth
- Vault ↔ Vault: TCP/8201/cluster replication (enterprise)

---

## Apache Cassandra

**Components:**
- Cassandra Nodes - Distributed wide-column store (peer-to-peer)
- Seeds - Bootstrap nodes for cluster discovery
- Coordinator Node - Receives client request, routes to replicas
- Replica Nodes - Store partition data based on replication factor
- Snitch - Determines data center and rack topology
- Compaction - Background process merging SSTables
- Commitlog - Write-ahead log for durability
- Applications - CQL clients

**Key Connections:**
- Applications → Coordinator: CQL/9042/queries
- Coordinator → Replica Nodes: TCP/inter-node/read-write replicas
- Nodes ↔ Nodes: TCP/7000/gossip protocol, cluster state
- Nodes ↔ Nodes: TCP/7001/inter-node TLS communication
- Nodes → Seeds: TCP/7000/cluster bootstrap, discovery
- nodetool → Nodes: JMX/7199/administration

---

## Neo4j

**Components:**
- Neo4j Server - Graph database engine
- Core Servers - Read/write instances (causal cluster)
- Read Replicas - Scale-out read instances
- Bolt Protocol - Binary protocol for client communication
- Cypher Query Engine - Graph query processing
- Transaction Log - Write-ahead log for ACID
- Neo4j Browser - Web-based query interface
- Neo4j Bloom - Visual graph exploration
- Applications - Graph database clients

**Key Connections:**
- Applications → Neo4j: Bolt/7687/Cypher queries
- Neo4j Browser → Neo4j: HTTP/7474, Bolt/7687/queries
- Core ↔ Core: TCP/5000/Raft consensus, transaction sync
- Core → Read Replicas: TCP/6000/transaction streaming
- Read Replicas → Core: TCP/catch-up protocol
- Bloom → Neo4j: Bolt/7687/graph visualization queries

---

## Qdrant

**Components:**
- Qdrant Server - Vector similarity search engine
- Qdrant Cluster Nodes - Distributed vector storage (Raft consensus)
- Collections - Named vector spaces with configurable distance metrics
- Shards - Horizontal partitioning of collections
- Replicas - Shard redundancy across nodes
- WAL - Write-ahead log for durability
- HNSW Index - Approximate nearest neighbor index
- Payload Storage - Metadata associated with vectors
- Applications - Vector search clients

**Key Connections:**
- Applications → Qdrant: HTTP/6333, gRPC/6334/vector operations
- Qdrant ↔ Qdrant: TCP/6335/internal cluster communication
- Qdrant Nodes ↔ Nodes: Raft/consensus, shard replication
- ML Pipeline → Qdrant: HTTP, gRPC/upsert embeddings
- Search Service → Qdrant: HTTP, gRPC/similarity search
- Qdrant → Disk: local/persist collections, WAL, indexes

---

## Envoy / Istio

**Components:**
- Istiod (Control Plane) - Configuration, certificate management, service discovery
- Envoy Proxy (Data Plane) - Sidecar proxy for traffic management
- Ingress Gateway - External traffic entry point
- Egress Gateway - Controlled external traffic exit
- Pilot - Service discovery, traffic management config
- Citadel - Certificate authority, mTLS
- Galley - Configuration validation (deprecated, merged into Istiod)
- Kiali - Service mesh observability UI
- Jaeger - Distributed tracing

**Key Connections:**
- External Traffic → Ingress Gateway: HTTPS/incoming requests
- Ingress Gateway → Service Envoy: mTLS/route to service
- Service Envoy ↔ Service Envoy: mTLS/service-to-service traffic
- Envoy → Istiod: gRPC/xDS/receive config updates
- Istiod → Kubernetes API: HTTPS/watch services, endpoints
- Istiod → Envoy: gRPC/push certificates, policies
- Services → Egress Gateway: mTLS/external traffic
- Envoy → Jaeger: HTTP/report traces
- Kiali → Prometheus: HTTP/query metrics
- Kiali → Kubernetes API: HTTPS/read mesh topology

---

## ArgoCD

**Components:**
- API Server - REST/gRPC API, Web UI, CLI interface
- Repository Server - Clones Git repos, generates manifests
- Application Controller - Monitors apps, syncs desired state
- Redis - Caching and state storage
- Dex - OIDC authentication (optional)
- ApplicationSet Controller - Dynamic app generation
- Notifications Controller - Event notifications
- Git Repository - Source of truth for manifests

**Key Connections:**
- Users → API Server: HTTPS/UI, CLI operations
- API Server → Repository Server: gRPC/get manifests
- Repository Server → Git: HTTPS, SSH/clone repos
- Application Controller → Kubernetes API: HTTPS/apply manifests, watch resources
- Application Controller → Repository Server: gRPC/get desired state
- API Server → Redis: TCP/6379/cache, state
- API Server → Dex: HTTP/OIDC authentication
- Notifications Controller → Slack, Email, Webhook: HTTPS/send alerts

---

## OpenTelemetry

**Components:**
- OTel SDK - Instrumentation libraries (traces, metrics, logs)
- OTel Collector - Receives, processes, exports telemetry
- Receivers - Ingest data (OTLP, Jaeger, Prometheus, etc.)
- Processors - Transform data (batch, filter, attributes)
- Exporters - Send data to backends (Jaeger, Prometheus, etc.)
- Auto-instrumentation Agent - Automatic code instrumentation
- Jaeger/Tempo - Trace storage and query
- Prometheus - Metrics storage
- Loki - Log aggregation

**Key Connections:**
- Applications (SDK) → Collector: OTLP/4317 gRPC, 4318 HTTP/send telemetry
- Auto-agent → Application: in-process/instrument code
- Collector → Jaeger: gRPC/14250, HTTP/export traces
- Collector → Tempo: OTLP/export traces
- Collector → Prometheus: HTTP/remote write metrics
- Collector → Loki: HTTP/export logs
- Collector ↔ Collector: OTLP/pipeline chaining
- Grafana → Jaeger, Prometheus, Loki: HTTP/query telemetry

---

## Apache Spark

**Components:**
- Driver Program - User application, creates SparkContext
- SparkContext - Coordinates execution, connects to cluster
- Cluster Manager - YARN, Kubernetes, Mesos, or Standalone
- Executors - JVM processes running tasks on workers
- Tasks - Units of work on data partitions
- DAG Scheduler - Converts job to stages
- Task Scheduler - Assigns tasks to executors
- Spark UI - Web interface for monitoring
- Data Sources - HDFS, S3, Kafka, JDBC, Iceberg, Delta

**Key Connections:**
- Driver → Cluster Manager: RPC/request resources
- Cluster Manager → Workers: RPC/launch executors
- Driver → Executors: RPC/send tasks, collect results
- Executors ↔ Executors: TCP/shuffle data exchange
- Executors → Data Sources: HDFS, S3, JDBC/read-write data
- Driver → Spark UI: HTTP/4040/expose metrics
- spark-submit → Cluster Manager: RPC/submit application

---

## Apache Iceberg / Parquet

**Components:**
- Iceberg Table - Table format with metadata and data files
- Metadata Files - JSON files tracking table schema, partitions, snapshots
- Manifest Lists - Point to manifest files for each snapshot
- Manifest Files - Track data files and their statistics
- Data Files (Parquet) - Columnar storage format
- Catalog (Hive, Glue, REST, Nessie) - Table namespace management
- Query Engines - Spark, Trino, Flink, Dremio
- Object Storage - S3, HDFS, GCS, Azure Blob

**Key Connections:**
- Query Engine → Catalog: HTTP, Thrift/resolve table location
- Query Engine → Metadata Files: S3, HDFS/read table metadata
- Query Engine → Manifest Files: S3, HDFS/get data file list
- Query Engine → Parquet Files: S3, HDFS/read columnar data
- Write Engine → Object Storage: S3, HDFS/write Parquet files
- Write Engine → Catalog: HTTP/commit new snapshot
- Compaction Job → Object Storage: S3, HDFS/rewrite data files
- Nessie → Object Storage: S3/Git-like versioned catalog

---

## HDFS

**Components:**
- NameNode - Metadata server, namespace management
- Secondary NameNode - Checkpoint helper (not standby)
- Standby NameNode - HA failover (with JournalNodes)
- JournalNodes - Shared edit log for HA (quorum-based)
- DataNodes - Block storage on local disks
- ZKFC (ZooKeeper Failover Controller) - Automatic NameNode failover
- ZooKeeper - Coordination for HA
- Balancer - Redistributes blocks across DataNodes
- Clients - HDFS applications

**Key Connections:**
- Clients → NameNode: RPC/8020/get block locations, metadata ops
- Clients → DataNodes: TCP/9866/read-write blocks
- DataNodes → NameNode: RPC/heartbeat, block reports
- DataNodes ↔ DataNodes: TCP/block replication
- NameNode → JournalNodes: RPC/8485/write edit logs
- Standby NameNode → JournalNodes: RPC/8485/read edit logs
- ZKFC → ZooKeeper: TCP/2181/leader election
- ZKFC → NameNode: RPC/health monitoring
- Balancer → NameNode: RPC/get block distribution
- Balancer → DataNodes: TCP/move blocks
