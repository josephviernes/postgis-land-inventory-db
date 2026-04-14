# Transforming Geospatial Data into a Structured PostGIS Database: A Land Parcel Inventory System

By Joseph Viernes

## Project Overview
This project transforms raw geospatial datasets (e.g., GeoPackage, Shapefiles) into a structured PostGIS database to support land parcel inventory and spatial analysis. It enables efficient storage, querying, and management of land asset data for real estate, site selection, and industrial applications such as solar power development.

By centralizing data within a spatially enabled PostgreSQL/PostGIS database, the system improves query performance, ensures data consistency, and eliminates repetitive data processing tasks such as rejoining attribute tables during updates.

Updates to spatial features (e.g., polygons) and attribute data can be managed interactively through GIS tools like QGIS or directly via SQL queries, providing a flexible, scalable, and integrated solution for maintaining land parcel datasets.

## Data Description
The dataset used in this project is a fictional and anonymized representation of land parcels in Ilocos Region, Philippines. It is intended solely for demonstration and development purposes.

All spatial features and attribute data have been modified to remove any real-world references, ensuring that no sensitive or identifiable information is included.

## Data Transformation

[Link to full schema.sql](schema.sql)

The transformation layer focuses on cleaning, standardizing, and enriching the raw staging table (ilocos1_row_lots) to prepare it for analytical modelling.

Key steps include schema adjustments, removal of irrelevant attributes, fixing inconsistent column names, and generating surrogate keys for relational mapping.

```sql
-- Add new operational and relational columns
ALTER TABLE ilocos1_row_lots ADD COLUMN team_lead VARCHAR(30);
ALTER TABLE ilocos1_row_lots ADD COLUMN assigned_vehicle VARCHAR(20);
ALTER TABLE ilocos1_row_lots ADD COLUMN ro_id SMALLINT;
ALTER TABLE ilocos1_row_lots ADD COLUMN team_id SMALLINT;

-- Remove unnecessary route columns
ALTER TABLE ilocos1_row_lots 
DROP COLUMN "ROUTE 1",
DROP COLUMN "ROUTE 2",
DROP COLUMN "ROUTE 3",
DROP COLUMN "ROUTE 4",
DROP COLUMN "ROUTE 5";

-- Fix inconsistent naming
ALTER TABLE ilocos1_row_lots
RENAME COLUMN "REGISTERED OWNER2" TO registered_owner;
```

A surrogate key (ro_id) is generated using a window function to uniquely identify registered owners.

```sql
UPDATE ilocos1_row_lots i
SET ro_id = r.rk
FROM (
    SELECT "CORRIDOR INDEX",
           DENSE_RANK() OVER (ORDER BY registered_owner DESC) AS rk
    FROM ilocos1_row_lots
) r
WHERE i."CORRIDOR INDEX" = r."CORRIDOR INDEX";
```

## Data Modelling

[Link to full schema.sql](schema.sql)

The cleaned dataset is transformed into a relational schema following a fact–dimension structure. This improves query efficiency, reduces redundancy, and supports analytical use cases.

### Fact Table

The ilocos1_lots table serves as the central fact table containing spatial, transactional, and descriptive attributes.

```sql
CREATE TABLE ilocos1_lots AS
SELECT
    fid,
    geom,
    "CORRIDOR INDEX" AS corridor_index,
    "REPORTED" AS date_reported,
    "LAST UPDATE" AS last_update,
    "PROVINCE" AS province,
    "MUNICIPALITY" AS municipality,
    "LATITUDE" AS latitude,
    "LONGITUDE" AS longitude,
    registered_owner,
    "LOT NUMBER" AS lot_number,
    "SURVEY NUMBER" AS survey_number,
    "LOT AREA (SQM)" AS lot_area,
    "NEGO PHASE" AS nego_phase,
    "PRICE (SALE)" AS price_sale,
    "PAYMENT TERMS (SALE)" AS payment_terms_sale,
    "PRICE (LEASE)" AS price_lease,
    "CONTRACT TERMS (LEASE)" AS contract_terms_lease,
    "NEGO COUNT" AS nego_count,
    "SLOPE" AS slope,
    ro_id,
    team_id,
    "TITLE" AS title,
    "TAX DEC" AS tax_dec
FROM ilocos1_row_lots;
```

### Dimension Tables

Separate dimension tables are created to normalize repeated entities and improve relational integrity.

```sql
-- Registered Owner dimension
CREATE TABLE ilocos1_ro AS
SELECT DISTINCT
    ro_id,
    registered_owner,
    "MOBILE NO" AS contact_number
FROM ilocos1_row_lots;

-- Team dimension
CREATE TABLE ilocos1_teams AS
SELECT DISTINCT
    team_id,
    team_lead,
    assigned_vehicle
FROM ilocos1_row_lots;
```

### Relationships & Constraints

[ER DIAGRAM](er_diagram.png)

Primary and foreign keys enforce relational integrity between fact and dimension tables.

```sql
-- Primary keys
ALTER TABLE ilocos1_lots ADD PRIMARY KEY (corridor_index);
ALTER TABLE ilocos1_ro ADD PRIMARY KEY (id);
ALTER TABLE ilocos1_teams ADD PRIMARY KEY (id);

-- Foreign keys
ALTER TABLE ilocos1_lots
ADD CONSTRAINT fk_ro
FOREIGN KEY (ro_id) REFERENCES ilocos1_ro(id);

ALTER TABLE ilocos1_lots
ADD CONSTRAINT fk_team
FOREIGN KEY (team_id) REFERENCES ilocos1_teams(id);
```

### Data Integrity & Automation

Constraints and identity columns ensure uniqueness and automated ID generation.

```sql
-- Prevent duplicate owners
ALTER TABLE ilocos1_ro
ADD CONSTRAINT unique_owner_contact UNIQUE (registered_owner);

-- Auto-generate IDs
ALTER TABLE ilocos1_ro ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;
ALTER TABLE ilocos1_teams ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;
ALTER TABLE ilocos1_lots ALTER COLUMN corridor_index ADD GENERATED ALWAYS AS IDENTITY;
```

## Sample Queries

```sql
-- QUERY: Retrieve enriched lot data
-- PURPOSE: Join fact table with dimension tables to produce a complete analytical view
SELECT 
    lots.corridor_index,
    lots.province,
    lots.municipality,
    lots.nego_phase,
    lots.lot_area,
    lots.price_sale,
    lots.payment_terms_sale,
    teams.team_lead,
    ro.registered_owner,
    ro.contact_number
FROM ilocos1_lots lots
LEFT JOIN ilocos1_teams teams
    ON lots.team_id = teams.id
LEFT JOIN ilocos1_ro ro
    ON lots.ro_id = ro.id
WHERE lots.nego_phase = 'OPEN TO SALE OR LEASE';


-- INSERT: Add new registered owner (dimension table)
-- PURPOSE: Insert a new owner record while preventing duplicates using ON CONFLICT handling
INSERT INTO ilocos1_ro (registered_owner, contact_number)
VALUES ('Vince Masuka', 9281921101)
ON CONFLICT (registered_owner) DO NOTHING;


-- INSERT: Load new lot records into fact table
-- PURPOSE: Insert transactional lot data and resolve foreign keys using dimension lookups
INSERT INTO ilocos1_lots (
    province,
    municipality,
    lot_area,
    nego_phase,
    ro_id,
    team_id
)
SELECT
    v.province,
    v.municipality,
    v.lot_area,
    v.nego_phase,
    ro.id,
    teams.id
FROM (
    VALUES
        ('ILOCOS NORTE', 'MARCOS', 12300, 'OPEN TO SALE OR LEASE', 'Vince Masuka', 'Joseph'),
        ('ILOCOS NORTE', 'MARCOS', 15450, 'OPEN TO SALE OR LEASE', 'Vince Masuka', 'Joseph')
) AS v(province, municipality, lot_area, nego_phase, registered_owner, team_lead)
JOIN ilocos1_ro ro 
    ON ro.registered_owner = v.registered_owner
JOIN ilocos1_teams teams 
    ON teams.team_lead = v.team_lead;


-- UPDATE: Correct foreign key mapping
-- PURPOSE: Fix incorrect or placeholder owner references after data insertion
UPDATE ilocos1_lots
SET ro_id = 26
WHERE ro_id = 1819;


-- DELETE: Remove invalid or unused dimension record
-- PURPOSE: Clean up orphaned or incorrectly inserted owner data
DELETE FROM ilocos1_ro
WHERE id = 1819;
```

## Key Learnings

### Geospatial Data Ingestion (QGIS → PostGIS)
Learned how to load geospatial datasets (GeoPackage, Shapefile, CSV, etc.) from QGIS and other sources into a PostGIS-enabled PostgreSQL database, enabling centralized spatial data storage and management.

### Geospatial Data Export (PostGIS → QGIS)
Practiced retrieving and visualizing data from PostGIS back into QGIS for mapping, validation, and spatial analysis.

### Database Navigation and Management
Gained familiarity with PostgreSQL GUI tools (e.g., pgAdmin / DB Browser), including schema browsing, table inspection, and query execution.

### Database Administration (Roles, Grants, and Privileges)
Learned how to manage database security by creating roles, assigning permissions, and controlling access to schemas and tables.

### Data Cleaning, Transformation, and Optimization
Applied techniques for cleaning raw geospatial data, standardizing attributes, improving data quality, and optimizing table structure and performance.

### SQL Querying for Geospatial Analysis
Developed skills in writing SQL queries for filtering, joining, aggregating, and analyzing spatial and non-spatial data in PostGIS.

## Future Improvements

### Automated Data Ingestion Pipeline

Currently, data loading may be manual or semi-manual. This can be improved by building an automated ingestion pipeline (e.g., scheduled ETL using Python, Airflow, or Kestra) to continuously update the PostGIS database from source files or APIs.

### Versioning of Geospatial Data

Introduce version control for spatial datasets (e.g., tracking changes over time or using temporal tables) to support historical analysis and rollback capability.

### Containerization of the Workflow

Use Docker to containerize the database + tools (PostGIS, pgAdmin, ETL scripts) for easier setup, reproducibility, and deployment.

### Orchestration and Monitoring

Add orchestration (Airflow/Kestra) plus logging and monitoring to track pipeline runs, failures, and data freshness.

## Acknowledgements

- CS50 (Harvard University) – for foundational courses in Python and SQL  
- edX – for hosting the CS50 learning platform