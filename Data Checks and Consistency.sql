
--=============================================
-- 1. Duplicate Checks
--=============================================
-- Account Table

SELECT account_id, COUNT(*) FROM account
GROUP BY account_id
HAVING COUNT(*) > 1;

-- Client Table
SELECT client_id, COUNT(*) FROM client
GROUP BY client_id
HAVING COUNT(*) > 1;

-- Loan table
SELECT loan_id,COUNT(*) FROM loan
GROUP BY loan_id
HAVING COUNT(*) > 1;

-- Card Table
SELECT card_id, COUNT(*) FROM card
GROUP BY card_id
HAVING COUNT(*) > 1;

-- Order Table
SELECT order_id, COUNT(*) FROM [Order]
GROUP BY order_id
HAVING COUNT(*) > 1;

-- Transaction Table
SELECT trans_id, COUNT(*) FROM Transaction_Merged
GROUP BY trans_id
HAVING COUNT(*) > 1;

-- Disposition
SELECT disp_id, COUNT(*) FROM Disp
GROUP BY disp_id
HAVING COUNT(*) > 1;

--===============================
-- 2. Null Value Checks
--===============================

SELECT
    SUM(CASE WHEN account_id   IS NULL THEN 1 ELSE 0 END) AS null_account_id,
    SUM(CASE WHEN district_id  IS NULL THEN 1 ELSE 0 END) AS null_district_id,
    SUM(CASE WHEN frequency    IS NULL THEN 1 ELSE 0 END) AS null_frequency,
    SUM(CASE WHEN date         IS NULL THEN 1 ELSE 0 END) AS null_date,
    SUM(CASE WHEN Account_type IS NULL THEN 1 ELSE 0 END) AS null_account_type
FROM account;

-- Client Table
SELECT
    SUM(CASE WHEN client_id    IS NULL THEN 1 ELSE 0 END) AS null_client_id,
    SUM(CASE WHEN birth_number IS NULL THEN 1 ELSE 0 END) AS null_birth_number,
    SUM(CASE WHEN district_id  IS NULL THEN 1 ELSE 0 END) AS null_district_id
FROM client;

-- Disposition Table
SELECT
    SUM(CASE WHEN disp_id    IS NULL THEN 1 ELSE 0 END) AS null_disp_id,
    SUM(CASE WHEN client_id  IS NULL THEN 1 ELSE 0 END) AS null_client_id,
    SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS null_account_id,
    SUM(CASE WHEN type       IS NULL THEN 1 ELSE 0 END) AS null_type
FROM disp;

-- Card Table
SELECT
    SUM(CASE WHEN card_id      IS NULL THEN 1 ELSE 0 END) AS null_card_id,
    SUM(CASE WHEN disp_id      IS NULL THEN 1 ELSE 0 END) AS null_disp_id,
    SUM(CASE WHEN type         IS NULL THEN 1 ELSE 0 END) AS null_type,
    SUM(CASE WHEN issued_date  IS NULL THEN 1 ELSE 0 END) AS null_issued_date
FROM card;

-- Loan Table
SELECT
    SUM(CASE WHEN loan_id    IS NULL THEN 1 ELSE 0 END) AS null_loan_id,
    SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS null_account_id,
    SUM(CASE WHEN date       IS NULL THEN 1 ELSE 0 END) AS null_date,
    SUM(CASE WHEN amount     IS NULL THEN 1 ELSE 0 END) AS null_amount,
    SUM(CASE WHEN duration   IS NULL THEN 1 ELSE 0 END) AS null_duration,
    SUM(CASE WHEN payments   IS NULL THEN 1 ELSE 0 END) AS null_payments,
    SUM(CASE WHEN status     IS NULL THEN 1 ELSE 0 END) AS null_status
FROM loan;

--  Transaction_Merged
SELECT
    SUM(CASE WHEN trans_id   IS NULL THEN 1 ELSE 0 END) AS null_trans_id,
    SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS null_account_id,
    SUM(CASE WHEN Date       IS NULL THEN 1 ELSE 0 END) AS null_date,
    SUM(CASE WHEN Type       IS NULL THEN 1 ELSE 0 END) AS null_type,
    SUM(CASE WHEN amount     IS NULL THEN 1 ELSE 0 END) AS null_amount,
    SUM(CASE WHEN balance    IS NULL THEN 1 ELSE 0 END) AS null_balance,
    SUM(CASE WHEN operation  IS NULL THEN 1 ELSE 0 END) AS null_operation,
    SUM(CASE WHEN Purpose    IS NULL THEN 1 ELSE 0 END) AS null_purpose,
    SUM(CASE WHEN bank       IS NULL THEN 1 ELSE 0 END) AS null_bank
FROM Transaction_Merged;

--=========================================
-- 3. REFERENTIAL INTEGRITY CHECKS
--=========================================
-- Transactions with account_id NOT in Account table
SELECT COUNT(*) AS orphan_transactions
FROM Transaction_Merged t
LEFT JOIN account a ON t.account_id = a.account_id
WHERE a.account_id IS NULL;

-- Loans with account_id NOT in Account table
SELECT COUNT(*) AS orphan_loans
FROM loan l
LEFT JOIN account a ON l.account_id = a.account_id
WHERE a.account_id IS NULL;

-- Orders with account_id NOT in Account table
SELECT COUNT(*) AS orphan_orders
FROM [order] o
LEFT JOIN account a ON o.account_id = a.account_id
WHERE a.account_id IS NULL;

-- Cards with disp_id NOT in Disposition table
SELECT COUNT(*) AS orphan_cards
FROM card c
LEFT JOIN disp d ON c.disp_id = d.disp_id
WHERE d.disp_id IS NULL;

-- Dispositions with client_id NOT in Client table
SELECT COUNT(*) AS orphan_disp_clients
FROM disp d
LEFT JOIN client cl ON d.client_id = cl.client_id
WHERE cl.client_id IS NULL;

-- Dispositions with account_id NOT in Account table
SELECT COUNT(*) AS orphan_disp_accounts
FROM disp d
LEFT JOIN account a ON d.account_id = a.account_id
WHERE a.account_id IS NULL;

-- Accounts with district_id NOT in District table
SELECT COUNT(*) AS invalid_district_in_account
FROM account a
LEFT JOIN district di ON a.district_id = di.A1
WHERE di.A1 IS NULL;

-- Clients with district_id NOT in District table
SELECT COUNT(*) AS invalid_district_in_client
FROM client cl
LEFT JOIN district di ON cl.district_id = di.A1
WHERE di.A1 IS NULL;

--======================================
-- 4. DATE VALIDATION CHECKS
--======================================

----- Loan Date Before Account Date
SELECT * FROM Loan l
JOIN Account a
ON l.account_id = a.account_id
WHERE l.date < a.date;

---- Card Issued Before Account Creation
SELECT * FROM Card c
JOIN Disp d
ON c.disp_id = d.disp_id
JOIN Account a
ON d.account_id = a.account_id
WHERE c.issued_date < a.date;

--==========================================
 ---- 5.Negative Transaction Amount ----
 --==========================================

-- Negative Loan Amount
SELECT COUNT(*) AS non_positive_transaction_amount
FROM Transaction_Merged
WHERE amount <= 0;

-- Negative Transaction Amount
SELECT COUNT(*) AS non_positive_transaction_amount
FROM Transaction_Merged
WHERE Transaction_Merged.balance <= 0;

-- Negative Balance
SELECT count(*) as negative_balance FROM Transaction_Merged
WHERE balance < 0;

--======================================
-- 6. LOAN STATUS VALIDATION 
--======================================
SELECT * FROM Loan
WHERE status NOT IN ('A','B','C','D');

--======================================
-- 7. Card Type Validation
--======================================

Select Distinct(type) from card;

--======================================
-- 8. Account frequency Validation
--======================================
Select Distinct(frequency) from account;

--======================================
-- 9. Transaction Type Validation
--======================================
Select Distinct(Type) from Transaction_Merged;

--======================================
-- 10. OUTLIER CHECKS
--======================================

-- Top 10 Highest Transactions
SELECT TOP 10 * FROM Transaction_Merged
ORDER BY amount DESC;

-- Top 10 Highest Loans
SELECT TOP 10 * FROM Loan
ORDER BY amount DESC;

--======================================
-- 11. MISSING BUSINESS ATTRIBUTES
--======================================

-- Missing Purpose
SELECT COUNT(*) AS MissingPurpose FROM Transaction_Merged
WHERE Purpose IS NULL;

-- Missing Bank
SELECT COUNT(*) AS MissingBank FROM Transaction_Merged
WHERE Bank IS NULL;

-- Missing Account Pattern
SELECT COUNT(*) AS MissingAccountPattern
FROM Transaction_Merged
WHERE account_pattern_id IS NULL;

Select * from Transaction_Merged

-- ============================================================
-- 12: Birth_number validation
-- ============================================================

-- Validate birth_number length (should be 6 digits YYMMDD or YYMM+50DD)
-- birth_number stored as numeric; length should be 6
SELECT COUNT(*) AS invalid_birth_number_length
FROM client
WHERE LEN(CAST(birth_number AS VARCHAR)) NOT IN (5, 6);

-- Extract and validate gender from birth_number
-- Females: month portion > 50 (e.g., 515 means May female)
SELECT
    client_id,
    birth_number,
    CAST(LEFT(CAST(birth_number AS VARCHAR(10)), 2) AS INT) AS birth_year,
    CAST(SUBSTRING(CAST(birth_number AS VARCHAR(10)), 3, 2) AS INT) AS month_raw,
    CASE
        WHEN CAST(SUBSTRING(CAST(birth_number AS VARCHAR(10)), 3, 2) AS INT) > 50 THEN 'F'
        ELSE 'M'
    END AS derived_gender
FROM client
ORDER BY client_id;

-- Check for invalid month values after gender decoding
SELECT COUNT(*) AS invalid_month_in_birth_number
FROM client
WHERE
    CAST(SUBSTRING(CAST(birth_number AS VARCHAR(10)), 3, 2) AS INT)
    NOT BETWEEN 1 AND 12
    AND
    CAST(SUBSTRING(CAST(birth_number AS VARCHAR(10)), 3, 2) AS INT)
    NOT BETWEEN 51 AND 62;

-- Loan amount must be positive
SELECT COUNT(*) AS non_positive_loan_amount
FROM loan
WHERE amount <= 0;

--======================================
-- 12. Final Data Quality Summary
--======================================
-- DATA QUALITY SUMMARY
SELECT 'Account' AS TableName, COUNT(*) AS RecordCount FROM account
UNION ALL
SELECT 'Client', COUNT(*) FROM client
UNION ALL
SELECT 'Disposition', COUNT(*) FROM disp
UNION ALL
SELECT 'Card', COUNT(*) FROM card
UNION ALL
SELECT 'Loan', COUNT(*) FROM loan
UNION ALL
SELECT 'Order', COUNT(*) FROM [order]
UNION ALL
SELECT 'Transaction_Merged', COUNT(*) FROM Transaction_Merged
UNION ALL
SELECT 'District',COUNT(*) FROM district;


--=======================
--Quicks Fixes
--=======================

-- Fixing the dates in issued column under
/* ALTER VIEW vw_Card_Clean AS
SELECT
    card_id,
    disp_id,
    type,
    CONVERT(date,
           '19' + LEFT(issued,2) + '-' +
           SUBSTRING(issued,3,2) + '-' +
           SUBSTRING(issued,5,2)
          ) AS issued_date
FROM Card;

ALTER TABLE Card
ADD issued_date DATE;

UPDATE Card
SET issued_date =
CONVERT(date,
       '19' + LEFT(issued,2) + '-' +
       SUBSTRING(issued,3,2) + '-' +
       SUBSTRING(issued,5,2)
      );

ALTER TABLE Card
DROP COLUMN issued; */

-- Merging Six year Transaction Data
/* SELECT *
INTO Transaction_Merged
FROM trnx_16
WHERE 1 = 0;

INSERT INTO Transaction_Merged
SELECT * FROM trnx_16;

INSERT INTO Transaction_Merged
SELECT * FROM trnx_17;

INSERT INTO Transaction_Merged
SELECT * FROM trnx_18;

INSERT INTO Transaction_Merged
SELECT * FROM trnx_19;

INSERT INTO Transaction_Merged
SELECT * FROM trnx_20;

INSERT INTO Transaction_Merged
SELECT * FROM trnx_21;

SELECT COUNT(*) FROM Transaction_Merged; */

Select * from client

Alter table Client
Add derived_gender CHAR(1);

UPDATE Client
SET derived_gender =
CASE
    WHEN CAST(SUBSTRING(CAST(birth_number AS VARCHAR(10)),3,2) AS INT) > 50
        THEN 'F'
    ELSE 'M'
END;
