# ClickHouse Documentation Index

> Source: clickhouse-docs repo (732 files)
> Last updated: 2025-12-07
> Commit: 26f5e3eb179e290ff622b70b2315aead7dccb6c1

---

## Data Modeling
*Table design, schemas, projections, denormalization*

- **Overview** `docs/data-modeling/index.md`
- **Schema Design** `docs/data-modeling/schema-design.md` - Designing schemas for optimal query performance
- **Denormalization** `docs/data-modeling/denormalization.md` - Storing related data in single tables
- **Backfilling** `docs/data-modeling/backfilling.md` - Strategies for historical data

### Projections
- **Using Projections** `docs/data-modeling/projections/1_projections.md`
- **MVs vs Projections** `docs/data-modeling/projections/2_materialized-views-versus-projections.md`

---

## Materialized Views
*Pre-computed aggregations and transformations*

- **Overview** `docs/materialized-view/index.md`
- **Incremental MVs** `docs/materialized-view/incremental-materialized-view.md` - Compute at insert time
- **Refreshable MVs** `docs/materialized-view/refreshable-materialized-view.md` - Periodic full refresh

---

## Managing Data
*Updates, deletes, and data lifecycle*

### Core Concepts
- **Parts** `docs/managing-data/core-concepts/parts.md` - How MergeTree organizes data

### Operations
- **Deleting Data** `docs/managing-data/deleting-data/index.md`
- **Updating Data** `docs/managing-data/updating-data/index.md`
- **Truncate** `docs/managing-data/truncate.md`

---

## Best Practices
*Performance optimization and recommended patterns*

- **Overview** `docs/best-practices/index.md`
- **Choosing a Primary Key** `docs/best-practices/choosing_a_primary_key.md` - Critical for performance
- **Selecting Data Types** `docs/best-practices/select_data_type.md` - LowCardinality, Nullable, etc.
- **Use Materialized Views** `docs/best-practices/use_materialized_views.md`
- **Minimize Joins** `docs/best-practices/minimize_optimize_joins.md` - Denormalization strategies
- **Partitioning Keys** `docs/best-practices/partitioning_keys.mdx`
- **Insert Strategy** `docs/best-practices/selecting_an_insert_strategy.md` - Batch vs async
- **Data Skipping Indices** `docs/best-practices/using_data_skipping_indices.md` - Bloom filters, minmax
- **Avoid Mutations** `docs/best-practices/avoid_mutations.md` - Why UPDATEs are expensive
- **Avoid OPTIMIZE FINAL** `docs/best-practices/avoid_optimize_final.md`
- **JSON Type** `docs/best-practices/json_type.md` - Working with semi-structured data
- **Hardware Sizing** `docs/best-practices/sizing-and-hardware-recommendations.md`

---

## Dictionary
*External lookups for enrichment*

- **Overview** `docs/dictionary/index.md`

---

## Data Compression
*Storage optimization*

- **Compression Overview** `docs/data-compression/compression-in-clickhouse.md`
- **Compression Modes** `docs/data-compression/compression-modes.md` - LZ4, ZSTD, codecs

---

## Integrations

### Data Ingestion

#### ClickPipes (Cloud)
- **Overview** `docs/integrations/data-ingestion/clickpipes/index.md`
- **Kafka** `docs/integrations/data-ingestion/clickpipes/kafka/index.md`
- **Postgres CDC** `docs/integrations/data-ingestion/clickpipes/postgres/index.md`
- **MySQL CDC** `docs/integrations/data-ingestion/clickpipes/mysql/index.md`
- **MongoDB** `docs/integrations/data-ingestion/clickpipes/mongodb/index.md`
- **Object Storage** `docs/integrations/data-ingestion/clickpipes/object-storage/index.md`
- **Kinesis** `docs/integrations/data-ingestion/clickpipes/kinesis.md`

#### ETL Tools
- **dbt** `docs/integrations/data-ingestion/etl-tools/dbt/index.md` - Data transformation
- **Airbyte** `docs/integrations/data-ingestion/etl-tools/airbyte-and-clickhouse.md`
- **Fivetran** `docs/integrations/data-ingestion/etl-tools/fivetran/index.md`
- **dlt** `docs/integrations/data-ingestion/etl-tools/dlt-and-clickhouse.md`
- **Apache NiFi** `docs/integrations/data-ingestion/etl-tools/nifi-and-clickhouse.md`
- **Vector** `docs/integrations/data-ingestion/etl-tools/vector-to-clickhouse.md`
- **Apache Beam** `docs/integrations/data-ingestion/etl-tools/apache-beam.md`

#### Kafka
- **Overview** `docs/integrations/data-ingestion/kafka/index.md`
- **Kafka Table Engine** `docs/integrations/data-ingestion/kafka/kafka-table-engine.md`
- **Kafka Connect Sink** `docs/integrations/data-ingestion/kafka/kafka-clickhouse-connect-sink.md`
- **Confluent** `docs/integrations/data-ingestion/kafka/confluent/index.md`
- **MSK** `docs/integrations/data-ingestion/kafka/msk/index.md`

#### Object Storage
- **S3** `docs/integrations/data-ingestion/s3/index.md`
- **S3 Performance** `docs/integrations/data-ingestion/s3/performance.md`
- **GCS** `docs/integrations/data-ingestion/gcs/index.md`
- **MinIO** `docs/integrations/data-ingestion/s3-minio.md`

#### Data Formats
- **Overview** `docs/integrations/data-ingestion/data-formats/intro.md`
- **JSON** `docs/integrations/data-ingestion/data-formats/json/intro.md`
- **Parquet** `docs/integrations/data-ingestion/data-formats/parquet.md`
- **CSV/TSV** `docs/integrations/data-ingestion/data-formats/csv-tsv.md`
- **Arrow/Avro/ORC** `docs/integrations/data-ingestion/data-formats/arrow-avro-orc.md`

#### Databases
- **PostgreSQL** `docs/integrations/data-ingestion/dbms/postgresql/connecting-to-postgresql.md`
- **DynamoDB** `docs/integrations/data-ingestion/dbms/dynamodb/index.md`
- **JDBC** `docs/integrations/data-ingestion/dbms/jdbc-with-clickhouse.md`
- **ODBC** `docs/integrations/data-ingestion/dbms/odbc-with-clickhouse.md`

#### Cloud Platforms
- **Apache Spark** `docs/integrations/data-ingestion/apache-spark/index.md`
- **AWS Glue** `docs/integrations/data-ingestion/aws-glue/index.md`
- **Azure Data Factory** `docs/integrations/data-ingestion/azure-data-factory/index.md`
- **Google Dataflow** `docs/integrations/data-ingestion/google-dataflow/dataflow.md`

### Data Sources (Table Engines)
- **Iceberg** `docs/integrations/data-sources/table_engines/iceberg.md`
- **Delta Lake** `docs/integrations/data-sources/table_engines/deltalake.md`
- **Hudi** `docs/integrations/data-sources/table_engines/hudi.md`
- **MongoDB** `docs/integrations/data-sources/table_engines/mongodb.md`
- **PostgreSQL** `docs/integrations/data-sources/postgres.md`
- **MySQL** `docs/integrations/data-sources/mysql.md`

### Visualization
- **Overview** `docs/integrations/data-visualization/index.md`
- **Grafana** `docs/integrations/data-visualization/grafana/index.md`
- **Tableau** `docs/integrations/data-visualization/tableau/tableau-and-clickhouse.md`
- **Superset** `docs/integrations/data-visualization/superset-and-clickhouse.md`
- **Metabase** `docs/integrations/data-visualization/metabase-and-clickhouse.md`
- **Power BI** `docs/integrations/data-visualization/powerbi-and-clickhouse.md`
- **Looker** `docs/integrations/data-visualization/looker-and-clickhouse.md`

### Language Clients
- **Python** `docs/integrations/language-clients/python/index.md`
- **Java** `docs/integrations/language-clients/java/index.md`
- **Go** `docs/integrations/language-clients/go/index.md`
- **Node.js** `docs/integrations/language-clients/nodejs.md`
- **Rust** `docs/integrations/language-clients/rust.md`

---

## Guides

### Developer Guides
- **Lightweight Deletes** `docs/guides/developer/lightweight-delete.md`
- **Deduplication** `docs/guides/developer/deduplication.md`
- **ReplacingMergeTree** `docs/guides/developer/replacing-merge-tree.md`
- **Cascading MVs** `docs/guides/developer/cascading-materialized-views.md`
- **TTL** `docs/guides/developer/ttl.md` - Time-to-live for data expiration
- **Debugging Memory** `docs/guides/developer/debugging-memory-issues.md`
- **Query Analyzer** `docs/guides/developer/understanding-query-execution-with-the-analyzer.md`

### Best Practices (Detailed)
- **Sparse Primary Indexes** `docs/guides/best-practices/sparse-primary-indexes.md`
- **Skipping Indexes** `docs/guides/best-practices/skipping-indexes.md`
- **Query Optimization** `docs/guides/best-practices/query-optimization.md`
- **Async Inserts** `docs/guides/best-practices/asyncinserts.md`
- **Bulk Inserts** `docs/guides/best-practices/bulkinserts.md`

### Starter Guides
- **Creating Tables** `docs/guides/starter_guides/creating-tables.md`
- **Inserting Data** `docs/guides/starter_guides/inserting-data.md`
- **Writing Queries** `docs/guides/starter_guides/writing-queries.md`
- **Working with Arrays** `docs/guides/starter_guides/working_with_arrays.md`
- **Working with Joins** `docs/guides/starter_guides/working_with_joins.md`

### SRE / Operations
- **SSL Configuration** `docs/guides/sre/configuring-ssl.md`
- **Network Ports** `docs/guides/sre/network-ports.md`
- **Scaling Clusters** `docs/guides/sre/scaling-clusters.md`
- **Keeper** `docs/guides/sre/keeper/index.md`
- **User Management** `docs/guides/sre/user-management/index.md`

---

## Getting Started

### Quick Start
- **Cloud** `docs/getting-started/quick-start/cloud.mdx`
- **Self-hosted** `docs/getting-started/quick-start/oss.mdx`

### Installation
- **Overview** `docs/getting-started/install/install.mdx`
- **Docker** `docs/getting-started/install/docker.md`
- **Debian/Ubuntu** `docs/getting-started/install/debian_ubuntu.md`
- **macOS** `docs/getting-started/install/macos.md`

### Example Datasets
- **NYC Taxi** `docs/getting-started/example-datasets/nyc-taxi.md`
- **UK Price Paid** `docs/getting-started/example-datasets/uk-price-paid.md`
- **GitHub Events** `docs/getting-started/example-datasets/github-events.md`
- **Stack Overflow** `docs/getting-started/example-datasets/stackoverflow.md`

---

## Concepts
- **OLAP** `docs/concepts/olap.md`
- **Why ClickHouse is Fast** `docs/concepts/why-clickhouse-is-so-fast.mdx`
- **Glossary** `docs/concepts/glossary.md`

---

## Cloud
*ClickHouse Cloud specific documentation*

### Migration Guides
- **Overview** `docs/cloud/onboard/02_migrate/01_migration_guides/01_overview.md`
- **From PostgreSQL** `docs/cloud/onboard/02_migrate/01_migration_guides/02_postgres/index.md`
- **From BigQuery** `docs/cloud/onboard/02_migrate/01_migration_guides/03_bigquery/index.md`
- **From Snowflake** `docs/cloud/onboard/02_migrate/01_migration_guides/04_snowflake/index.md`
- **From Redshift** `docs/cloud/onboard/02_migrate/01_migration_guides/06_redshift/index.md`
- **From Elasticsearch** `docs/cloud/onboard/02_migrate/01_migration_guides/05_elastic/01_overview.md`
- **OSS to Cloud** `docs/cloud/onboard/02_migrate/01_migration_guides/07_OSS_to_Cloud/01_clickhouse-to-cloud.md`

### Features
- **Auto Scaling** `docs/cloud/features/04_infrastructure/automatic_scaling/01_auto_scaling.md`
- **SharedMergeTree** `docs/cloud/features/04_infrastructure/shared-merge-tree.md`
- **Backups** `docs/cloud/features/08_backups.md`

### Security
- **Access Management** `docs/cloud/guides/security/01_cloud_access_management/index.md`
- **Private Networking** `docs/cloud/guides/security/02_connectivity/private_networking/index.md`
- **CMEK** `docs/cloud/guides/security/04_cmek.md`

---

## Use Cases

### Observability
- **Overview** `docs/use-cases/observability/index.md`
- **ClickStack** `docs/use-cases/observability/clickstack/index.md`

### Time Series
- **Overview** `docs/use-cases/time-series/index.md`

### AI/ML
- **Overview** `docs/use-cases/AI_ML/index.md`
- **MCP** `docs/use-cases/AI_ML/MCP/index.md` - Model Context Protocol

### Data Lake
- **Overview** `docs/use-cases/data_lake/index.md`

---

## chDB
*Embedded ClickHouse for Python*

- **Overview** `docs/chdb/index.md`
- **Getting Started** `docs/chdb/getting-started.md`
- **Python API** `docs/chdb/api/python.md`
- **Query Pandas** `docs/chdb/guides/querying-pandas.md`
- **Query Parquet** `docs/chdb/guides/querying-parquet.md`

---

## FAQ
- **General** `docs/faq/general/index.md`
- **Operations** `docs/faq/operations/index.md`
- **Integration** `docs/faq/integration/index.md`
- **Use Cases** `docs/faq/use-cases/index.md`
