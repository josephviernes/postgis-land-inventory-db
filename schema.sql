-- altering table to include the following columns
ALTER TABLE ilocos1_row_lots ADD COLUMN team_lead VARCHAR(30)
ALTER TABLE ilocos1_row_lots ADD COLUMN assigned_vehicle VARCHAR(20)
ADD COLUMN ro_id SMALLINT,
ADD COLUMN team_id SMALLINT

-- drop columns
ALTER TABLE ilocos1_row_lots 
DROP COLUMN "ROUTE 1",
DROP COLUMN "ROUTE 2",
DROP COLUMN "ROUTE 3",
DROP COLUMN "ROUTE 4",
DROP COLUMN "ROUTE 5"

--renaming column to fix typo
ALTER TABLE ilocos1_row_lots
RENAME COLUMN "REGISTERED OWNER2" TO registered_owner

--filling ro_id with values based on the DENSE_RANK() of registered_owner (putting a distinct id based on registered_owner values)
UPDATE ilocos1_row_lots i
SET ro_id = r.rk
FROM (
    SELECT "CORRIDOR INDEX", DENSE_RANK() OVER (ORDER BY registered_owner DESC) AS rk
    FROM ilocos1_row_lots
) r
WHERE i."CORRIDOR INDEX" = r."CORRIDOR INDEX"


--create a new table independent of the staging table; this would served as the fact table
CREATE TABLE ilocos1_lots AS
	SELECT fid, geom, "CORRIDOR INDEX" AS "corridor_index", "REPORTED" AS "date_reported", "LAST UPDATE" AS "last_update", "PROVINCE" as "province", "MUNICIPALITY" AS "municipality", "LATITUDE" AS "latitude", "LONGITUDE" AS "longitude",
	registered_owner, "LOT NUMBER" AS "lot_number", "SURVEY NUMBER" AS "survey_number", "LOT AREA (SQM)" AS "lot_area", "NEGO PHASE" AS "nego_phase", "PRICE (SALE)" AS "price_sale", "PAYMENT TERMS (SALE)" AS "payment_terms_sale",
    "PRICE (LEASE)" AS "price_lease", "CONTRACT TERMS (LEASE)" AS "contract_terms_lease", "NEGO COUNT" AS "nego_count", "SLOPE" AS "slope", ro_id, team_id,
    "TITLE" AS "title", "TAX DEC" AS "tax_dec"
FROM ilocos1_row_lots

--create dimension table containing the lot owner's data
CREATE TABLE ilocos1_ro AS
    SELECT ro_id, registered_owner, "MOBILE NO" AS "contact_number"
FROM ilocos1_row_lots

--create dimension table containing the team's data
CREATE TABLE ilocos1_team AS
    SELECT team_id, team_lead, assigned_vehicle
FROM ilocos1_row_lots


-- creating new dimension tables with distinct id
CREATE TABLE ilocos1_teams AS
SELECT DISTINCT
	team_id,
	team_lead,
	assigned_vehicle
FROM ilocos1_team;

ALTER TABLE ilocos1_ro RENAME TO ilocos1_roo;

CREATE TABLE ilocos1_ro AS
SELECT DISTINCT ON (id)
	ro_id,
	registered_owner,
	contact_number
FROM ilocos1_roo;

ALTER TABLE ilocos1_teams
RENAME COLUMN team_id TO id;

ALTER TABLE ilocos1_ro
RENAME COLUMN ro_id TO id;

DROP TABLE ilocos1_team, ilocos_roo;


-- adding a primary key
ALTER TABLE ilocos1_lots
ADD PRIMARY KEY (corridor_index);

ALTER TABLE ilocos1_teams
ADD PRIMARY KEY (id);

ALTER TABLE ilocos1_ro
ADD PRIMARY KEY (id);

--referenced the foreign key in the dimension tables
ALTER TABLE ilocos1_lots
ADD CONSTRAINT fk_ro
FOREIGN KEY (ro_id)
REFERENCES ilocos1_ro(id);

ALTER TABLE ilocos1_lots
ADD CONSTRAINT fk_team
FOREIGN KEY (team_id)
REFERENCES ilocos1_teams(id);


-- granting read access to another user
GRANT USAGE ON SCHEMA land_row TO senior_gis;

GRANT SELECT
ON ALL TABLES
IN SCHEMA land_row
TO senior_gis;

CREATE VIEW secured_lots AS
SELECT
	lots.corridor_index,
	lots.geom,
	lots.province,
	lots.municipality,
	lots.nego_phase,
	lots.price_sale,
	lots.price_lease,
	teams.team_lead,
	ro.registered_owner
FROM ilocos1_lots lots
LEFT JOIN ilocos1_teams teams
	ON lots.team_id = teams.id
LEFT JOIN ilocos1_ro ro
	ON lots.ro_id = ro.id
WHERE nego_phase LIKE 'SECURED%';

CREATE VIEW osol_lots AS
SELECT
	lots.corridor_index,
	lots.geom,
	lots.province,
	lots.municipality,
	lots.nego_phase,
	lots.price_sale,
	lots.price_lease,
	teams.team_lead,
	ro.registered_owner
FROM ilocos1_lots lots
LEFT JOIN ilocos1_teams teams
	ON lots.team_id = teams.id
LEFT JOIN ilocos1_ro ro
	ON lots.ro_id = ro.id
WHERE nego_phase LIKE 'OPEN%';

-- automatically generate new id to any added rows
ALTER TABLE ilocos1_ro
ALTER COLUMN id
ADD GENERATED ALWAYS AS IDENTITY;

ALTER TABLE ilocos1_teams
ALTER COLUMN id
ADD GENERATED ALWAYS AS IDENTITY;

ALTER TABLE ilocos1_lots
ALTER COLUMN corridor_index
ADD GENERATED ALWAYS AS IDENTITY;

-- adding a unique constraint to avoid duplication
ALTER TABLE ilocos1_ro
ADD CONSTRAINT unique_owner_contact
UNIQUE (registered_owner);

-- fixes the ERROR: duplicate key value violates unique constraint "ilocos1_lots_pkey" Key (corridor_index)=(1) already exists. 
SELECT setval(
    pg_get_serial_sequence('ilocos1_ro', 'id'),
    (SELECT MAX(id) FROM ilocos1_ro)
);

SELECT setval(
    pg_get_serial_sequence('ilocos1_lots', 'corridor_index'),
    (SELECT MAX(corridor_index) FROM ilocos1_lots)
);