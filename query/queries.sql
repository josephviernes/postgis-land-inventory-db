-- selecting data from the tables
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

-- inserting new entries to the ilocos1_ro dim table. The inserted new entry is then referenced on the next query of fact table
INSERT INTO ilocos1_ro (registered_owner, contact_number)
VALUES ('Vince Masuka', 9281921101)
ON CONFLICT (registered_owner) DO NOTHING;

-- inserting new rows to the fact table
INSERT INTO ilocos1_lots (province, municipality, lot_area, nego_phase, ro_id, team_id)
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
) as v(corridor_index, province, municipality, lot_area, nego_phase, registered_owner, team_lead)
JOIN ilocos1_ro ro ON ro.registered_owner = v.registered_owner
JOIN ilocos1_teams teams ON teams.team_lead = v.team_lead;

-- updating the newly added rows
UPDATE ilocos1_lots
SET ro_id = 26
WHERE ro_id = 1819;

-- delete the newly added but unused rows
DELETE FROM ilocos1_ro
WHERE id = 1819;

-- insert latest ground report entries into the land_row.ground_reports_refined table
INSERT INTO land_row.ground_reports_refined (
	index_no,
	report_date,
	province,
	municipality,
	tax_dec,
	title,
	lot_number,
	survey_number,
	lot_area,
	nego_phase,
	price_sale,
	payment_terms_sale,
	price_lease,
	contract_terms_lease,
	registered_owner,
	mobile_number,
	team_id,
	remarks
)
SELECT
	index_no::BIGINT,
	report_date::DATE,
	province::VARCHAR,
	municipality::VARCHAR,
	tax_dec::VARCHAR,
	title::VARCHAR,
	lot_number::VARCHAR,
	survey_number::VARCHAR,
	lot_area::NUMERIC,
	nego_phase::VARCHAR,
	price_sale::NUMERIC,
	payment_terms_sale::VARCHAR,
	price_lease::NUMERIC,
	contract_terms_lease::VARCHAR,
	registered_owner::VARCHAR,
	mobile_number::VARCHAR,
	team_no::SMALLINT,
	remarks::TEXT
FROM land_row.ground_reports_staging
ON CONFLICT (index_no)
DO UPDATE
SET
	report_date = EXCLUDED.report_date,
	province = EXCLUDED.province,
	municipality = EXCLUDED.municipality,
	tax_dec = EXCLUDED.tax_dec,
	title = EXCLUDED.title,
	lot_number = EXCLUDED.lot_number,
	survey_number = EXCLUDED.survey_number,
	lot_area = EXCLUDED.lot_area,
	nego_phase = EXCLUDED.nego_phase,
	price_sale = EXCLUDED.price_sale,
	payment_terms_sale = EXCLUDED.payment_terms_sale,
	price_lease = EXCLUDED.price_lease,
	contract_terms_lease = EXCLUDED.contract_terms_lease,
	registered_owner = EXCLUDED.registered_owner,
	mobile_number = EXCLUDED.mobile_number,
	team_id = EXCLUDED.team_id,
	remarks = EXCLUDED.remarks;

-- insert new registered owners into the ilocos1_ro table
INSERT INTO land_row.ilocos1_ro (
	registered_owner,
	contact_number
)
SELECT
    grf.registered_owner,
    grf.mobile_number
FROM land_row.ground_reports_refined grf
LEFT JOIN land_row.ilocos1_ro ro
    ON grf.registered_owner = ro.registered_owner
WHERE ro.registered_owner IS NULL;

-- update ro_id referencing ilocos1_ro table
UPDATE land_row.ground_reports_refined grf
SET grf.ro_id = ro.id
FROM land_row.ilocos1_ro ro
WHERE grf.registered_owner = ro.registered_owner;