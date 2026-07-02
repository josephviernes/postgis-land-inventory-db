-- show list of roles
SELECT rolname, rolpassword FROM pg_roles;

-- show a role's privileges
SELECT 
    nspname AS schema_name,
    rolname AS grantee,
    CASE 
        WHEN has_schema_privilege(rolname, nspname, 'USAGE') THEN 'USAGE' 
        ELSE '' 
    END ||
    CASE 
        WHEN has_schema_privilege(rolname, nspname, 'CREATE') THEN 
            CASE WHEN has_schema_privilege(rolname, nspname, 'USAGE') THEN ', CREATE' ELSE 'CREATE' END
        ELSE '' 
    END AS privileges
FROM 
    pg_namespace,
    pg_roles
WHERE 
    rolname = 'senior_gis' -- Replace with the role you are testing
    AND nspname NOT LIKE 'pg_%' -- Filters out system schemas
    AND nspname != 'information_schema';



--SECURE; revoke default public access
REVOKE ALL ON DATABASE gis FROM PUBLIC;
REVOKE ALL ON SCHEMA land_row FROM PUBLIC;



-- create a new group role
CREATE ROLE db_owner;

-- create a new user role that can login
CREATE ROLE harrypotter WITH LOGIN PASSWORD 'expelliarmus';

-- making harrypotter a member of db_owner group
GRANT db_owner TO harrypotter;

-- grant privileges to the group
-- allow connection
GRANT CONNECT ON DATABASE gis TO db_owner;

-- allow schema usage
GRANT USAGE ON SCHEMA land_row TO db_owner;

-- allow table privileges
GRANT CREATE ON SCHEMA land_row to db_owner



-- create new group role
CREATE ROLE gis_developer;

-- creating a new user role that can login
CREATE ROLE josephviernes WITH LOGIN PASSWORD '20220445';

-- making josephviernes a member of the gis_developer group
GRANT gis_developer TO josephviernes;

-- grant privileges to the group
-- allow connection
GRANT CONNECT ON DATABASE gis TO gis_developer;

-- allow schema usage
GRANT USAGE ON SCHEMA land_row TO gis_developer;

-- allow table privileges
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA land_row TO gis_developer;

--default privileges
ALTER DEFAULT PRIVILEGES FOR ROLE harrypotter IN SCHEMA land_row 
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON TABLES TO gis_developer;