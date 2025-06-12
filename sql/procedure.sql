DELIMITER //
CREATE PROCEDURE GenerateASNLineNumber(
    IN p_owner VARCHAR(255),
    IN p_username VARCHAR(255),
    OUT p_asn_number VARCHAR(50),
    OUT p_line_number VARCHAR(10),
    OUT p_status VARCHAR(20),
    OUT p_message TEXT
)
main_proc: BEGIN
    DECLARE v_current_full VARCHAR(50);      -- Full current number from NEXTUP (e.g., ASN10000001)
    DECLARE v_next_full VARCHAR(50);         -- Full next number from NEXTUP (e.g., ASN10000002)
    DECLARE v_ending_full VARCHAR(50);       -- Full ending number from NEXTUP (e.g., ASN99999999)
    DECLARE v_prefix VARCHAR(10);             -- Current prefix (ASN, BSN, etc.)
    DECLARE v_max_lines INT;                 -- max lines from the nextup table
    DECLARE v_record_type VARCHAR(10);       -- The TYPE from NEXTUP table
    
    -- Working variables
    DECLARE v_current_lines INT DEFAULT 0;             --lines assigned to current ASN
    DECLARE v_last_owner VARCHAR(255);                 -- to compare whether to generate a new ASN
    DECLARE v_need_new_asn BOOLEAN DEFAULT FALSE;      -- if need a new ASN
    DECLARE v_line_number INT DEFAULT 1;               -- assign line numbers
    DECLARE v_max_line_current_owner INT DEFAULT 0;    -- max line used by current owner
    DECLARE v_total_records_current_asn INT DEFAULT 0; -- total records for current ASN 
    
    -- For incrementing numbers
    DECLARE v_current_numeric VARCHAR(20);    -- Numeric part extracted from current
    DECLARE v_next_numeric VARCHAR(20);       -- Numeric part extracted from next
    DECLARE v_new_current_numeric BIGINT;     -- updated numeric part from current
    DECLARE v_new_next_numeric BIGINT;        -- updated numeric part from next 
    DECLARE v_new_current_full VARCHAR(50);   -- full value with prefix for current
    DECLARE v_new_next_full VARCHAR(50);      -- full value with prefix for next
    
    -- Variables for maximum limit checking 
    DECLARE v_ending_numeric VARCHAR(20);     -- Extracted numeric portion
    DECLARE v_current_num_value BIGINT;       -- numeric value of ASN
    DECLARE v_ending_num_value BIGINT;        -- numeric max value
    
    -- Error handling
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        GET DIAGNOSTICS CONDITION 1 p_message = MESSAGE_TEXT;
        SET p_status = 'ERROR';
        SET p_asn_number = NULL;
        SET p_line_number = NULL;
    END;
    
    SET p_status = 'SUCCESS';
    SET p_message = 'ASN and line generated successfully';
    
    START TRANSACTION;
    
    -- Get data from NEXTUP table - dynamically find the active record
    SELECT 
        CURRENTNUMBER,           
        NEXTNUMBER,             
        ENDINGNUMBER,           
        NUMBEROFLINES,          
        COALESCE(TRIM(PREFIX), '') as PREFIX, 
        TYPE                    
    INTO 
        v_current_full, 
        v_next_full, 
        v_ending_full,
        v_max_lines,
        v_prefix,
        v_record_type
    FROM NEXTUP 
    FOR UPDATE;
    
    IF v_current_full IS NULL THEN
        SET p_status = 'ERROR';
        SET p_message = 'No configuration found in NEXTUP table';
        ROLLBACK;
        LEAVE main_proc;
    END IF;
    
    -- Extract numeric parts from full numbers
    -- For example if ASN10000005, extract 10000005
    IF LENGTH(v_prefix) > 0 THEN
        SET v_current_numeric = SUBSTRING(v_current_full, LENGTH(v_prefix) + 1);
        SET v_next_numeric = SUBSTRING(v_next_full, LENGTH(v_prefix) + 1);
    ELSE
        SET v_current_numeric = v_current_full;
        SET v_next_numeric = v_next_full;
    END IF;
    
    -- Check maximum limit (need to handle different prefixes in ending number)
    -- Extract numeric part from ending number for comparison
    
    -- Extract numeric part from ending number
    IF LENGTH(v_prefix) > 0 AND v_ending_full LIKE CONCAT(v_prefix, '%') THEN
        SET v_ending_numeric = SUBSTRING(v_ending_full, LENGTH(v_prefix) + 1);
    ELSE
        -- If ending number has different prefix, extract all the digits
        SET v_ending_numeric = REGEXP_REPLACE(v_ending_full, '[^0-9]', '');
    END IF;
    
    SET v_current_num_value = CAST(v_current_numeric AS UNSIGNED);
    SET v_ending_num_value = CAST(v_ending_numeric AS UNSIGNED);
    
    IF v_current_num_value >= v_ending_num_value THEN
        SET p_status = 'ERROR';
        SET p_message = 'ASN sequence has reached maximum number';
        ROLLBACK;
        LEAVE main_proc;
    END IF;
    
    -- Check current ASN usage in DOWNLOADTABLE
    SELECT 
        COUNT(*) AS total_records,
        COALESCE(MAX(CASE WHEN OWNER = p_owner THEN CAST(LINENUMBER AS UNSIGNED) ELSE 0 END), 0),
        COUNT(CASE WHEN OWNER = p_owner THEN 1 ELSE NULL END),
        MAX(OWNER)
    INTO 
        v_total_records_current_asn,
        v_max_line_current_owner,
        v_current_lines,
        v_last_owner
    FROM DOWNLOADTABLE
    WHERE ASNNUMBER = v_current_full;
    
    -- Decision Logic: Reuse current ASN or get new one
    IF v_total_records_current_asn = 0 THEN
        -- Current ASN is unused - use it
        SET v_need_new_asn = FALSE;
        SET v_line_number = 1;
    ELSEIF v_last_owner = p_owner AND v_current_lines < v_max_lines THEN
        -- Same owner, can add more lines to current ASN
        SET v_need_new_asn = FALSE;
        SET v_line_number = v_max_line_current_owner + 1;
    ELSE
        -- Need new ASN (different owner OR max lines reached)
        SET v_need_new_asn = TRUE;
        SET v_line_number = 1;
    END IF;
    
    -- Execute decision and update NEXTUP if needed
    IF v_need_new_asn THEN
        -- Use next ASN and advance the sequence
        SET p_asn_number = v_next_full;
        SET p_line_number = LPAD(1, 4, '0');
        
        -- Calculate new current and next numbers
        SET v_new_current_numeric = CAST(v_next_numeric AS UNSIGNED);
        SET v_new_next_numeric = v_new_current_numeric + 1;
        
        -- Build new full numbers with current prefix
        IF LENGTH(v_prefix) > 0 THEN
            SET v_new_current_full = CONCAT(v_prefix, LPAD(v_new_current_numeric, LENGTH(v_current_numeric), '0'));
            SET v_new_next_full = CONCAT(v_prefix, LPAD(v_new_next_numeric, LENGTH(v_next_numeric), '0'));
        ELSE
            SET v_new_current_full = LPAD(v_new_current_numeric, LENGTH(v_current_numeric), '0');
            SET v_new_next_full = LPAD(v_new_next_numeric, LENGTH(v_next_numeric), '0');
        END IF;
        
        -- Boundary check
        IF v_new_current_numeric >= v_ending_num_value THEN
            SET p_status = 'ERROR';
            SET p_message = 'Next ASN would exceed maximum range';
            ROLLBACK;
            LEAVE main_proc;
        END IF;
        
        -- Update NEXTUP table with new full numbers - USE DYNAMIC TYPE
        UPDATE NEXTUP 
        SET 
            CURRENTNUMBER = v_new_current_full,     
            NEXTNUMBER = v_new_next_full,           
            DATEUPDATED = CURDATE(),
            USERUPDATED = p_username
        WHERE TYPE = v_record_type;  
        
    ELSE
        -- Reuse current ASN
        SET p_asn_number = v_current_full;
        SET p_line_number = LPAD(v_line_number, 4, '0');
    END IF;
    
    COMMIT;
END //
DELIMITER ;