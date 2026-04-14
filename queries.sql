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