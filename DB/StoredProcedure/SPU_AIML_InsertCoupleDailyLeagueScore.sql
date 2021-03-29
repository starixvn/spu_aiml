DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_InsertCoupleDailyLeagueScore`;

CREATE PROCEDURE `SPU_AIML_InsertCoupleDailyLeagueScore`(
	IN 	ip_DailyStats 		JSON,
    
    OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210316@Long.Luu
		Task:		Insert Couple Daily League Score [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210316@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertCoupleDailyLeagueScore ('[{"C1": 1, "C2": 1111, "LS": 1}]',@msg);    
	*/ 
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_DailyStats;    
	CREATE TEMPORARY TABLE Temp_DailyStats 
    (	 
			CustID1							BIGINT UNSIGNED	NOT NULL
		, 	CustID2							BIGINT UNSIGNED NOT NULL
		, 	LeagueScore						DECIMAL(10,4) NOT NULL
        , 	PRIMARY KEY	    PK_Temp_DailyStats_CustID1_CustID2(CustID1,CustID2) 
    );      
    
    INSERT INTO Temp_DailyStats(CustID1, CustID2, LeagueScore)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
		, 	tmpTable.LeagueScore
	FROM JSON_TABLE(ip_DailyStats,
		 "$[*]" COLUMNS(
			  CustID1 							BIGINT UNSIGNED		PATH "$.C1"
			, CustID2							BIGINT UNSIGNED		PATH "$.C2"
			, LeagueScore						DECIMAL(10,4)		PATH "$.LS"
		 )) AS tmpTable;  
        
	UPDATE SPU_AIML.CoupleDailyStats AS a
		INNER JOIN Temp_DailyStats AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	a.LeagueScore = t.LeagueScore;
        
    DROP TEMPORARY TABLE IF EXISTS Temp_DailyStats;
     
END$$