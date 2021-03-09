DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_InsertCoupleAccummulatedDaily`;

CREATE PROCEDURE `SPU_AIML_InsertCoupleAccummulatedDaily`(
	IN 	ip_AddUpStats 		JSON,
    
    OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20201204@Long.Luu
		Task:		Insert Couple Accummulated Daily [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20201204@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertCoupleAccummulatedDaily ('[{"C1": 43600693, "C2": 45, "TS": 1, "MS": 1, "LS": 0.8, "TJD": 1, "TJC": 3, "TJSC": 2, "BC": 20}]');    
	*/ 
    
    DECLARE lv_CurrentDateTime 	DATETIME DEFAULT NOW();

    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_AssociationStats;    
	CREATE TEMPORARY TABLE Temp_AssociationStats 
    (	 
		CustID1 					BIGINT UNSIGNED NOT NULL,
		CustID2 					BIGINT UNSIGNED NOT NULL,
		TotalTimeInterval 			INT UNSIGNED NOT NULL,
		TotalJoiningCombs 			INT UNSIGNED NOT NULL,
		TotalJoiningSuspiciousCombs INT UNSIGNED NOT NULL,
		MajorLeagueFrequency		VARCHAR(8000) NOT NULL,
		MinorLeagueFrequency		VARCHAR(8000) NOT NULL,
        IsNewCouple					BIT DEFAULT 1,
		PRIMARY KEY (CustID1,CustID2)
    );      
    
    INSERT INTO Temp_AssociationStats(CustID1, CustID2, TotalTimeInterval, TotalJoiningCombs, TotalJoiningSuspiciousCombs, MajorLeagueFrequency, MinorLeagueFrequency)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
		, 	tmpTable.TimeScore
        , 	tmpTable.MatchScore
        , 	tmpTable.LeagueScore
        , 	tmpTable.TotalJoiningDays
        , 	tmpTable.TotalJoiningCombs
        , 	tmpTable.TotalJoiningSuspiciousCombs
        ,	tmpTable.BetCount
	FROM JSON_TABLE(ip_DailyStats,
		 "$[*]" COLUMNS(
			  CustID1 							BIGINT UNSIGNED		PATH "$.C1"
			, CustID2							BIGINT UNSIGNED		PATH "$.C2"
			, TotalTimeInterval					INT UNSIGNED		PATH "$.TS"
            , TotalJoiningCombs					INT UNSIGNED		PATH "$.MS"
            , TotalJoiningSuspiciousCombs		INT UNSIGNED		PATH "$.LS"
            , MajorLeagueFrequency				SMALLINT			PATH "$.TJD"
            , MinorLeagueFrequency				SMALLINT			PATH "$.TJC"
		 )) AS tmpTable;  
    
    UPDATE Temp_AssociationStats AS t
		LEFT JOIN SPU_AIML.AssociationStats AS a ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
	SET t.IsNewCouple = 0
    WHERE a.CustID1 IS NOT NULL
		AND a.CustID2 IS NOT NULL;
        
	INSERT IGNORE INTO SPU_AIML.AssociationStats(CustID1, CustID2, TimeScore, MatchScore, LeagueScore, TotalJoiningDays, TotalJoiningCombs, TotalJoiningSuspiciousCombs, BetCount, LastModifiedDate, LastModifiedTime)
	SELECT 	t.CustID1
		, 	t.CustID2
        , 	t.TimeScore
        , 	t.MatchScore
        , 	t.LeagueScore
        , 	t.TotalJoiningDays
        , 	t.TotalJoiningCombs
        , 	t.TotalJoiningSuspiciousCombs
        ,	t.BetCount
        ,	ip_ScanDate
        ,	lv_CurrentDateTime
    FROM Temp_AssociationStats AS t
	WHERE IsNewCouple = 1;
	
    UPDATE SPU_AIML.AssociationStats AS a
		INNER JOIN Temp_AssociationStats AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	a.TimeScore = t.TimeScore
		,	a.MatchScore = t.MatchScore
        ,	a.LeagueScore = t.LeagueScore
        , 	a.TotalJoiningDays = t.TotalJoiningDays
        , 	a.TotalJoiningCombs = a.TotalJoiningCombs + t.TotalJoiningCombs
        , 	a.TotalJoiningSuspiciousCombs = a.TotalJoiningSuspiciousCombs + t.TotalJoiningSuspiciousCombs
        ,	a.BetCount = a.BetCount + t.BetCount
        ,	a.LastModifiedDate = ip_ScanDate
        ,	a.LastModifiedTime = lv_CurrentDateTime
    WHERE t.IsNewCouple = 0;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_AssociationStats;
     
END$$