DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_InsertCoupleDailyStats`;

CREATE PROCEDURE `SPU_AIML_InsertCoupleDailyStats`(
	IN 	ip_DailyStats 		JSON,
    
    OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210316@Long.Luu
		Task:		Insert Couple Daily Stats [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210316@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertCoupleDailyStats ('[{"C1": 1, "C2": 1111, "TI": 1, "TJC": 3, "TJSC": 2}]',@msg);    
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
		, 	TimeInterval					DECIMAL(10,4) NOT NULL
		, 	TotalJoiningCombs				SMALLINT NOT NULL
		, 	TotalJoiningSuspiciousCombs		SMALLINT NOT NULL
        ,	IsNewCouple						BIT DEFAULT 1
        , 	PRIMARY KEY	    PK_Temp_DailyStats_CustID1_CustID2(CustID1,CustID2) 
    );      
    
    INSERT INTO Temp_DailyStats(CustID1, CustID2, TimeInterval, TotalJoiningCombs, TotalJoiningSuspiciousCombs)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
		, 	tmpTable.TimeInterval
        , 	tmpTable.TotalJoiningCombs
        , 	tmpTable.TotalJoiningSuspiciousCombs
	FROM JSON_TABLE(ip_DailyStats,
		 "$[*]" COLUMNS(
			  CustID1 							BIGINT UNSIGNED		PATH "$.C1"
			, CustID2							BIGINT UNSIGNED		PATH "$.C2"
			, TimeInterval						DECIMAL(10,4)		PATH "$.TI"
            , TotalJoiningCombs					SMALLINT			PATH "$.TJC"
            , TotalJoiningSuspiciousCombs		SMALLINT			PATH "$.TJSC"
		 )) AS tmpTable;  
    
    UPDATE Temp_DailyStats AS t
		LEFT JOIN SPU_AIML.CoupleDailyStats AS a ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
	SET t.IsNewCouple = 0
    WHERE a.CustID1 IS NOT NULL
		AND a.CustID2 IS NOT NULL;
        
	INSERT INTO SPU_AIML.CoupleDailyStats(CustID1, CustID2, TimeInterval, TotalJoiningCombs, TotalJoiningSuspiciousCombs)
	SELECT 	t.CustID1
		, 	t.CustID2
        , 	t.TimeInterval
        , 	t.TotalJoiningCombs
        , 	t.TotalJoiningSuspiciousCombs
    FROM Temp_DailyStats AS t
	WHERE IsNewCouple = 1;
	
    UPDATE SPU_AIML.CoupleDailyStats AS a
		INNER JOIN Temp_DailyStats AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	a.TimeInterval = a.TimeInterval + t.TimeInterval
        , 	a.TotalJoiningCombs = a.TotalJoiningCombs + t.TotalJoiningCombs
        , 	a.TotalJoiningSuspiciousCombs = a.TotalJoiningSuspiciousCombs + t.TotalJoiningSuspiciousCombs
    WHERE t.IsNewCouple = 0;
    
    SELECT 	t.CustID1
		, 	t.CustID2
        , 	t.TimeInterval
        , 	t.TotalJoiningCombs
        , 	t.TotalJoiningSuspiciousCombs
    FROM Temp_DailyStats AS t
		INNER JOIN SPU_AIML.CoupleDailyStats AS a ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2;
        
    DROP TEMPORARY TABLE IF EXISTS Temp_DailyStats;
     
END$$