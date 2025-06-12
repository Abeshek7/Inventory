DELIMITER //
CREATE TRIGGER update_asn_on_prefix_change
    BEFORE UPDATE ON NEXTUP
    FOR EACH ROW
BEGIN
    DECLARE v_numeric_part BIGINT DEFAULT 0;
    DECLARE v_old_prefix VARCHAR(10) DEFAULT '';
    DECLARE v_new_prefix VARCHAR(10) DEFAULT '';
    DECLARE v_padding_length INT;
    
    -- Only process records where PREFIX is being changed (dynamic type checking)
    IF COALESCE(OLD.PREFIX, '') != COALESCE(NEW.PREFIX, '') THEN
        -- Normalize old and new prefixes
        SET v_old_prefix = COALESCE(OLD.PREFIX, '');
        SET v_new_prefix = COALESCE(NEW.PREFIX, '');
        
        -- Extract numeric part from CURRENTNUMBER
        IF LENGTH(v_old_prefix) > 0 AND OLD.CURRENTNUMBER LIKE CONCAT(v_old_prefix, '%') THEN
            -- Current number has a prefix, extract numeric part
            SET v_numeric_part = CAST(SUBSTRING(OLD.CURRENTNUMBER, LENGTH(v_old_prefix) + 1) AS UNSIGNED);
            SET v_padding_length = LENGTH(SUBSTRING(OLD.CURRENTNUMBER, LENGTH(v_old_prefix) + 1));
        ELSE
            -- Current number has no prefix or doesn't match expected format
            --  extract numeric part from the entire current number
            SET v_numeric_part = CAST(REGEXP_REPLACE(OLD.CURRENTNUMBER, '[^0-9]', '') AS UNSIGNED);
            -- Determine padding length from the numeric part
            SET v_padding_length = GREATEST(LENGTH(REGEXP_REPLACE(OLD.CURRENTNUMBER, '[^0-9]', '')), 8);
        END IF;
        
        -- valid numeric part
        IF v_numeric_part = 0 THEN
            SET v_numeric_part = 1;
        END IF;
        
        -- Increment the numeric part
        SET v_numeric_part = v_numeric_part + 1;
        
        --  minimum padding length
        SET v_padding_length = GREATEST(v_padding_length, 8);
        
        -- Build new CURRENTNUMBER and NEXTNUMBER with new prefix
        IF LENGTH(v_new_prefix) > 0 THEN
            SET NEW.CURRENTNUMBER = CONCAT(v_new_prefix, LPAD(v_numeric_part, v_padding_length, '0'));
            SET NEW.NEXTNUMBER = CONCAT(v_new_prefix, LPAD(v_numeric_part + 1, v_padding_length, '0'));
        ELSE
            SET NEW.CURRENTNUMBER = LPAD(v_numeric_part, v_padding_length, '0');
            SET NEW.NEXTNUMBER = LPAD(v_numeric_part + 1, v_padding_length, '0');
        END IF;
        
        -- Update timestamp
        SET NEW.DATEUPDATED = CURDATE();
        SET NEW.USERUPDATED = COALESCE(NEW.USERUPDATED, USER());
    END IF;
END //
DELIMITER ;