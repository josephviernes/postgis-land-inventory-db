class LoadMergeQueries:
        # Query to merge data from staging to refined table, with conflict handling
        ground_reports_refined_upsert_query = """

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
            FROM land_row.ground_reports_staging;
        """

        # insert new registered owners into the ilocos1_ro table
        insert_new_ro_query = """
            INSERT INTO land_row.ilocos1_ro (
                registered_owner,
                contact_number
            )
            SELECT DISTINCT ON (grf.registered_owner)
                grf.registered_owner,
                grf.mobile_number
            FROM land_row.ground_reports_refined grf
            LEFT JOIN land_row.ilocos1_ro ro
                ON grf.registered_owner = ro.registered_owner
            WHERE ro.registered_owner IS NULL;
            """
        # update ro_id referencing ilocos1_ro table
        fill_ro_id_query = """ 
            UPDATE land_row.ground_reports_refined grf
            SET ro_id = ro.id
            FROM land_row.ilocos1_ro ro
            WHERE grf.registered_owner = ro.registered_owner;
        """

        # updating the main table using the reports from refined table
        update_main_table_query = """
            -- STEP 1: Update existing records
            UPDATE land_row.ilocos1_lots main
            SET
                last_update = CASE WHEN main.date_reported IS NOT NULL THEN grf.report_date END,
                province = CASE WHEN grf.province IS NOT NULL AND grf.province != '' THEN grf.province ELSE main.province END,
                municipality = CASE WHEN grf.municipality IS NOT NULL AND grf.municipality != '' THEN grf.municipality ELSE main.municipality END,
                tax_dec = CASE WHEN grf.tax_dec IS NOT NULL AND grf.tax_dec != '' THEN grf.tax_dec ELSE main.tax_dec END,
                title = CASE WHEN grf.title IS NOT NULL AND grf.title != '' THEN grf.title ELSE main.title END,
                lot_number = CASE WHEN grf.lot_number IS NOT NULL AND grf.lot_number != '' THEN grf.lot_number ELSE main.lot_number END,
                survey_number = CASE WHEN grf.survey_number IS NOT NULL AND grf.survey_number != '' THEN grf.survey_number ELSE main.survey_number END,
                nego_phase = CASE WHEN grf.nego_phase IS NOT NULL AND grf.nego_phase != '' THEN grf.nego_phase ELSE main.nego_phase END,
                payment_terms_sale = CASE WHEN grf.payment_terms_sale IS NOT NULL AND grf.payment_terms_sale != '' THEN grf.payment_terms_sale ELSE main.payment_terms_sale END,
                contract_terms_lease = CASE WHEN grf.contract_terms_lease IS NOT NULL AND grf.contract_terms_lease != '' THEN grf.contract_terms_lease ELSE main.contract_terms_lease END,
                
                lot_area = CASE WHEN grf.lot_area IS NOT NULL THEN grf.lot_area ELSE main.lot_area END,
                price_sale = CASE WHEN grf.price_sale IS NOT NULL THEN grf.price_sale ELSE main.price_sale END,
                price_lease = CASE WHEN grf.price_lease IS NOT NULL THEN grf.price_lease ELSE main.price_lease END,
                ro_id = CASE WHEN grf.ro_id IS NOT NULL THEN grf.ro_id ELSE main.ro_id END,
                team_id = CASE WHEN grf.team_id IS NOT NULL THEN grf.team_id ELSE main.team_id END,
                
                remarks = CASE 
                    WHEN grf.remarks IS NULL OR grf.remarks = '' THEN main.remarks
                    WHEN main.remarks IS NULL OR main.remarks = '' THEN CURRENT_DATE::TEXT || ': ' || grf.remarks 
                    ELSE CURRENT_DATE::TEXT || ': ' || grf.remarks || chr(10) || chr(10) || main.remarks 
                END
            FROM land_row.ground_reports_refined grf
            WHERE main.index_no = grf.index_no; -- Only updates rows where IDs match


            -- STEP 2: Insert brand new records (Letting Postgres handle the auto-increment)
            INSERT INTO land_row.ilocos1_lots (
                -- index_no is omitted here entirely!
                date_reported, last_update, province, municipality, tax_dec, title, lot_number, 
                survey_number, lot_area, nego_phase, price_sale, payment_terms_sale, 
                price_lease, contract_terms_lease, ro_id, team_id, remarks
            )
            SELECT 
                grf.report_date, NULL, grf.province, grf.municipality, grf.tax_dec, grf.title, grf.lot_number, 
                grf.survey_number, grf.lot_area, grf.nego_phase, grf.price_sale, grf.payment_terms_sale, 
                grf.price_lease, grf.contract_terms_lease, grf.ro_id, grf.team_id, 
                CASE WHEN grf.remarks IS NOT NULL AND grf.remarks != '' THEN CURRENT_DATE::TEXT || ': ' || grf.remarks ELSE NULL END
            FROM land_row.ground_reports_refined grf
            WHERE grf.index_no IS NULL; -- Only captures completely new records

                -- archiving entries    
                INSERT INTO land_row.ground_reports_refined_records (
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
                    team_id::SMALLINT,
                    remarks::TEXT
                FROM land_row.ground_reports_refined;

                --clean-up staging table
                TRUNCATE TABLE land_row.ground_reports_refined_records;
        """