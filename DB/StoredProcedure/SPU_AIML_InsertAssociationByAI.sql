USE SPU_AIML;
DROP PROCEDURE IF EXISTS `SPU_AIML_InsertAssociationByAI`;

DELIMITER $$
CREATE DEFINER=`aimlOwner`@`%` PROCEDURE `SPU_AIML_InsertAssociationByAI`(
	IN 	ip_DailyStats 		JSON,
    
    OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20201204@Long.Luu
		Task:		Insert Association Stats [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20201204@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertAssociationByAI ('[{"C1": 43600693, "C2": 45, "S": 1}]', @ErrorMessage);    
	*/ 
    
    DECLARE lv_CurrentDateTime 	DATETIME DEFAULT NOW();

    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_AssociationStats;    
	CREATE TEMPORARY TABLE Temp_AssociationStats 
    (	 
			CustID1			BIGINT UNSIGNED	NOT NULL
		, 	CustID2			BIGINT UNSIGNED NOT NULL
		, 	Score			DECIMAL(10,4) NOT NULL
        , 	PRIMARY KEY	    PK_Temp_AssociationStats_CustID1_CustID2(CustID1,CustID2) 
    );      
    
    INSERT INTO Temp_AssociationStats(CustID1, CustID2, Score)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
		, 	tmpTable.Score
	FROM JSON_TABLE(ip_DailyStats,
		 "$[*]" COLUMNS(
			  CustID1 		BIGINT UNSIGNED		PATH "$.C1"
			, CustID2		BIGINT UNSIGNED		PATH "$.C2"
			, Score		DECIMAL(10,4)		PATH "$.S"
		 )) AS tmpTable;  
            
	INSERT IGNORE INTO SPU_AIML.AssociationByAI(CustID1, CustID2, Score, LastModifiedDate)
	SELECT 	t.CustID1
		, 	t.CustID2
        , 	t.Score
        ,	lv_CurrentDateTime
    FROM Temp_AssociationStats AS t;
	
    UPDATE SPU_AIML.AssociationByAI AS a
		INNER JOIN Temp_AssociationStats AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	a.Score = t.Score
        ,	a.LastModifiedDate = lv_CurrentDateTime;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_AssociationStats;
     
END$$