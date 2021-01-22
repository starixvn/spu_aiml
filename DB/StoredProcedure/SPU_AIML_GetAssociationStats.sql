CREATE DEFINER=`aimlOwner`@`%` PROCEDURE `SPU_AIML_GetAssociationStats`(
	IN 	ip_IsFirstRunOfTheDay 		BIT,
    IN	ip_BatchSize				INT UNSIGNED,
    
    OUT op_ErrorMessage 			VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20201204@Long.Luu
		Task:		Get New Association Stats [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20201204@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_GetAssociationStats(1, 5000);    
	*/ 
    
    DECLARE lv_CurrentDate 		DATE DEFAULT NOW();
    DECLARE lv_MinCustID1 		BIGINT UNSIGNED;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_AssociationStats;    
	CREATE TEMPORARY TABLE Temp_AssociationStats 
    (	 
			CustID1							BIGINT UNSIGNED	NOT NULL
		, 	CustID2							BIGINT UNSIGNED NOT NULL
		, 	TimeScore						DECIMAL(10,4) NOT NULL
		, 	MatchScore						DECIMAL(10,4) NOT NULL
		, 	LeagueScore						DECIMAL(10,4) NOT NULL
		, 	TotalJoinedDays					SMALLINT NOT NULL
		, 	TotalJoinedMatches				SMALLINT NOT NULL
		, 	TotalJoinedSuspiciousMatches	SMALLINT NOT NULL
        , 	BetCount						BIGINT UNSIGNED NOT NULL
        , 	PRIMARY KEY	    PK_Temp_AssociationStats_CustID1_CustID2(CustID1,CustID2) 
        , 	INDEX	    	IX_Temp_AssociationStats_IsNewCouple(IsNewCouple) 
    );      
    
    IF (ip_IsFirstRunOfTheDay = 1) THEN
		SELECT lv_MinCustID1 = 0;
    ELSE
		SELECT ParameterValue #CAST(ParameterValue AS BIGINT UNSIGNED)
        INTO lv_MinCustID1
        FROM SPU_AIML.SystemParameter 
        WHERE ParameterID = 2;
    END IF;
    
    INSERT INTO Temp_AssociationStats(CustID1, CustID2, TimeScore, MatchScore, LeagueScore, TotalJoinedDays, TotalJoinedMatches, TotalJoinedSuspiciousMatches, BetCount)
    SELECT 	s.CustID1
		, 	s.CustID2
		, 	s.TimeScore
        , 	s.MatchScore
        , 	s.LeagueScore
        , 	s.TotalJoinedDays
        , 	s.TotalJoinedMatches
        , 	s.TotalJoinedSuspiciousMatches
        ,	s.BetCount
	FROM SPU_AIML.AssociationStats AS s
    WHERE s.CustID1 > lv_MinCustID1
		AND s.LastModifiedDate = lv_CurrentDate
	ORDER BY s.CustID1 ASC
    LIMIT 0, ip_BatchSize;  
    
	UPDATE SPU_AIML.SystemParameter
    SET ParameterValue = (SELECT MAX(CustID1) FROM Temp_AssociationStats)
	WHERE ParameterID = 2;
    
    SELECT *
    FROM Temp_AssociationStats;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_AssociationStats;
     
END