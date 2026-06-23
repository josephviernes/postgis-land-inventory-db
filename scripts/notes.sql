        ground_reports_refined_upsert_query = 

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
            FROM ground_reports_staging;
        

        # insert new registered owners into the ilocos1_ro table
        insert_new_ro_query = 
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
            
        # update ro_id referencing ilocos1_ro table
        fill_ro_id_query =  
            UPDATE land_row.ground_reports_refined grf
            SET grf.ro_id = ro.id
            FROM land_row.ilocos1_ro ro
            WHERE grf.registered_owner = ro.registered_owner;
        

        -- updating the main table using the reports from refined table
       update_main_table_query =
            INSERT INTO land_row.ilocos1_lots (
                index_no, date_reported, last_update, province, municipality, tax_dec, title, lot_number, survey_number, lot_area, 
				nego_phase, price_sale, payment_terms_sale, price_lease, contract_terms_lease, ro_id, mobile_number, team_id, remarks
            )
            SELECT 
                grf.index_no::INT,
                grf.report_date, -- for new inserts
                NULL,            -- last_update starts as NULL new inserts
                grf.province, grf.municipality, grf.tax_dec, grf.title, grf.lot_number, grf.survey_number, grf.lot_area, grf.nego_phase, grf.price_sale, 
                grf.payment_terms_sale, grf.price_lease, grf.contract_terms_lease, grf.ro_id, grf.mobile_number, grf.team_id, grf.remarks
            FROM land_row.ground_reports_refined grf
            ON CONFLICT (index_no) DO UPDATE SET
                date_reported = CASE
                    WHEN ilocos1_lots.date_reported IS NULL THEN EXCLUDED.date_reported
                    ELSE ilocos1_lots.date_reported
                END,
                last_update = CASE
                    WHEN ilocos1_lots.date_reported IS NOT NULL THEN EXCLUDED.date_reported
                    ELSE ilocos1_lots.last_update
                END,
                province = CASE WHEN EXCLUDED.province IS NOT NULL AND EXCLUDED.province != '' THEN EXCLUDED.province ELSE ilocos1_lots.province END,
                municipality = CASE WHEN EXCLUDED.municipality IS NOT NULL AND EXCLUDED.municipality != '' THEN EXCLUDED.municipality ELSE ilocos1_lots.municipality END,
                tax_dec = CASE WHEN EXCLUDED.tax_dec IS NOT NULL AND EXCLUDED.tax_dec != '' THEN EXCLUDED.tax_dec ELSE ilocos1_lots.tax_dec END,
                title = CASE WHEN EXCLUDED.title IS NOT NULL AND EXCLUDED.title != '' THEN EXCLUDED.title ELSE ilocos1_lots.title END,
                lot_number = CASE WHEN EXCLUDED.lot_number IS NOT NULL AND EXCLUDED.lot_number != '' THEN EXCLUDED.lot_number ELSE ilocos1_lots.lot_number END,
                survey_number = CASE WHEN EXCLUDED.survey_number IS NOT NULL AND EXCLUDED.survey_number != '' THEN EXCLUDED.survey_number ELSE ilocos1_lots.survey_number END,
                lot_area = CASE WHEN EXCLUDED.lot_area IS NOT NULL AND EXCLUDED.lot_area != '' THEN EXCLUDED.lot_area ELSE ilocos1_lots.lot_area END,
                nego_phase = CASE WHEN EXCLUDED.nego_phase IS NOT NULL AND EXCLUDED.nego_phase != '' THEN EXCLUDED.nego_phase ELSE ilocos1_lots.nego_phase END,
                price_sale = CASE WHEN EXCLUDED.price_sale IS NOT NULL AND EXCLUDED.price_sale != '' THEN EXCLUDED.price_sale ELSE ilocos1_lots.price_sale END,
                payment_terms_sale = CASE WHEN EXCLUDED.payment_terms_sale IS NOT NULL AND EXCLUDED.payment_terms_sale != '' THEN EXCLUDED.payment_terms_sale ELSE ilocos1_lots.payment_terms_sale END,
                price_lease = CASE WHEN EXCLUDED.price_lease IS NOT NULL AND EXCLUDED.price_lease != '' THEN EXCLUDED.price_lease ELSE ilocos1_lots.price_lease END,
                contract_terms_lease = CASE WHEN EXCLUDED.contract_terms_lease IS NOT NULL AND EXCLUDED.contract_terms_lease != '' THEN EXCLUDED.contract_terms_lease ELSE ilocos1_lots.contract_terms_lease END,
                ro_id = CASE WHEN EXCLUDED.ro_id IS NOT NULL AND EXCLUDED.ro_id != '' THEN EXCLUDED.ro_id ELSE ilocos1_lots.ro_id END,
                mobile_number = CASE WHEN EXCLUDED.mobile_number IS NOT NULL AND EXCLUDED.mobile_number != '' THEN EXCLUDED.mobile_number ELSE ilocos1_lots.mobile_number END,
                team_id = CASE WHEN EXCLUDED.team_id IS NOT NULL AND EXCLUDED.team_id != '' THEN EXCLUDED.team_id ELSE ilocos1_lots.team_id END,
                remarks = CASE WHEN ilocos1_lots.remarks IS NULL OR ilocos1_lots.remarks = '' THEN CURRENT_DATE::TEXT || ': ' || EXCLUDED.remarks ELSE CURRENT_DATE::TEXT || ': ' || EXCLUDED.remarks || chr(10) || chr(10) || ilocos1_lots.remarks END
			;
        