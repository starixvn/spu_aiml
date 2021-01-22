CREATE DEFINER=`ctsOwner`@`%` PROCEDURE `SPU_AIML_ComputeDailyScore`(
    OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210115@Long.Luu
		Task:		Compute Daily Score [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210115@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_ComputeDailyScore();  
	*/ 

    DECLARE lv_CurrentDate 		DATE DEFAULT NOW();
    DECLARE lv_CurrentDateTime 	DATETIME DEFAULT NOW();
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
    SET SQL_SAFE_UPDATES = 0;
    
    SET @lv_CurrentDate 			= NOW();
    SET @lv_CurrentDateTime 	= NOW();
    
    SET SQL_SAFE_UPDATES = 0;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleScores;
	CREATE TEMPORARY TABLE Temp_CoupleScores (
			CustID1					BIGINT UNSIGNED
		,	CustID2							BIGINT UNSIGNED
		,	TimeScore						DECIMAL(10,4)
        ,	LeagueScore						DECIMAL(10,4)
		,	TotalJoinedSuspiciousMatches	INT UNSIGNED
        ,	TotalJoinedMatches				INT UNSIGNED
		,	MatchIDList						VARCHAR(4000)
        ,	BettypeList						VARCHAR(4000)
        ,	IsNewCouple						BIT DEFAULT 1
		,	PRIMARY KEY 	PK_Temp_CoupleScores(CustID1,CustID2)	
        , 	INDEX	    	IX_Temp_CoupleScores(IsNewCouple) 	
	);
       
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleLeagueStats;    
	CREATE TEMPORARY TABLE Temp_CoupleLeagueStats 
    (	 
			CustID1					BIGINT UNSIGNED	NOT NULL
		, 	CustID2					BIGINT UNSIGNED NOT NULL
		, 	LeagueID				INT UNSIGNED 
        ,	IsMajorLeague			BIT
		,	MatchCount				INT UNSIGNED DEFAULT 0
        ,	TotalMatchCount			INT UNSIGNED DEFAULT 0
        , 	PRIMARY KEY	    		PK_Temp_CoupleLeagueStats_CustID1_CustID2(CustID1,CustID2,LeagueID,IsMajorLeague) 
    );    
    
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleGini;    
	CREATE TEMPORARY TABLE Temp_CoupleGini 
    (	 
			CustID1					BIGINT UNSIGNED	NOT NULL
		, 	CustID2					BIGINT UNSIGNED NOT NULL
		, 	MajorGiniScore			DECIMAL(10,4) DEFAULT 1
        , 	MinorGiniScore			DECIMAL(10,4) DEFAULT 1
        , 	PRIMARY KEY	    		PK_Temp_CoupleGini_CustID1_CustID2(CustID1,CustID2) 
    );    
    
    /* TIME SCORE & MATCH SCORE */
    INSERT INTO Temp_CoupleScores(CustID1, CustID2, TimeScore, TotalJoinedSuspiciousMatches, TotalJoinedMatches, MatchIDList, BettypeList)
    SELECT 	CustID1
		, 	CustID2
		,	AVG(TimeScore) AS TimeScore
        ,	COUNT(1) AS TotalJoinedSuspiciousMatches
        ,	MAX(TotalJoinningCombs) AS TotalJoinedMatches
        ,	GROUP_CONCAT(MatchID) AS MatchIDList
        ,	GROUP_CONCAT(Bettype) AS BettypeList
    FROM SPU_AIML.AssociationStatsStaging
    GROUP BY CustID1, CustID2;
    
    /* LEAGUE SCORE */
    INSERT INTO Temp_CoupleLeagueStats(CustID1, CustID2, LeagueID, IsMajorLeague, MatchCount)
    SELECT CustID1, CustID2, LeagueID, IsMajorLeague, COUNT(1)
    FROM SPU_AIML.AssociationStatsStaging
    GROUP BY CustID1, CustID2, LeagueID, IsMajorLeague;
    
    UPDATE Temp_CoupleLeagueStats AS t
		INNER JOIN (
			SELECT CustID1, CustID2, IsMajorLeague, COUNT(1) AS TotalMatchCount
			FROM SPU_AIML.AssociationStatsStaging
			GROUP BY CustID1, CustID2, IsMajorLeague
        ) AS a ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2 AND t.IsMajorLeague = a.IsMajorLeague
	SET t.TotalMatchCount = a.TotalMatchCount;
    
    /* Calc Gini Score */
    INSERT INTO Temp_CoupleGini(CustID1, CustID2, MajorGiniScore)
    SELECT CustID1, CustID2,
		(1 - SUM(	CASE WHEN IsMajorLeague = 1 THEN (MatchCount/TotalMatchCount)*(MatchCount/TotalMatchCount)
					ELSE 0 END))
    FROM Temp_CoupleLeagueStats
    GROUP BY CustID1, CustID2;
    
    UPDATE Temp_CoupleGini AS g
		INNER JOIN (
			SELECT CustID1, CustID2, 
				(1 - SUM(	CASE WHEN IsMajorLeague = 0 THEN (MatchCount/TotalMatchCount)*(MatchCount/TotalMatchCount)
							ELSE 0 END)) AS MinorGiniScore
			FROM Temp_CoupleLeagueStats
			GROUP BY CustID1, CustID2
        ) AS t ON g.CustID1 = t.CustID1 AND g.CustID2 = t.CustID2
    SET g.MinorGiniScore = t.MinorGiniScore;
    
    /* Finalize LeagueScore  */
    UPDATE Temp_CoupleScores AS s
		INNER JOIN Temp_CoupleGini AS g ON s.CustID1 = g.CustID1 AND s.CustID2 = g.CustID2
	SET s.LeagueScore = CASE 	WHEN g.MinorGiniScore = 1 THEN (g.MajorGiniScore + 3/2) * (2/5)
								WHEN g.MajorGiniScore = 1 THEN (g.MinorGiniScore + 5/2) * (2/7)
								ELSE (3 * ((MinorGiniScore + 5/2) * (2/7) + 1) + ((g.MajorGiniScore + 3/2) * (2/5) + 2)) * (1/9)
						END;
   
    /* UPDATE SCORE */
    UPDATE Temp_CoupleScores AS t
		LEFT JOIN SPU_AIML.AssociationStats AS a ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
	SET t.IsNewCouple = 0
    WHERE a.CustID1 IS NOT NULL
		AND a.CustID2 IS NOT NULL;
    
    /* Update Association Stats */
	INSERT IGNORE INTO SPU_AIML.AssociationStats(CustID1, CustID2, TimeScore, MatchScore, LeagueScore, TotalJoinedDays, TotalJoinedMatches, TotalJoinedSuspiciousMatches, BetCount, LastModifiedDate, LastModifiedTime)
	SELECT 	t.CustID1
		, 	t.CustID2
        , 	t.TimeScore
        , 	CAST(t.TotalJoinedSuspiciousMatches/t.TotalJoinedMatches AS DECIMAL(10,4)) AS MatchScore
        , 	t.LeagueScore
        , 	1 AS TotalJoinedDays
        , 	t.TotalJoinedMatches 
        , 	t.TotalJoinedSuspiciousMatches
        ,	0 AS BetCount
        ,	@lv_CurrentDate
        ,	@lv_CurrentDateTime
    FROM Temp_CoupleScores AS t
	WHERE IsNewCouple = 1;
    
    UPDATE SPU_AIML.AssociationStats AS a
		INNER JOIN Temp_CoupleScores AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	a.TimeScore = a.TimeScore + t.TimeScore
		,	a.MatchScore = a.MatchScore + CAST(t.TotalJoinedSuspiciousMatches/t.TotalJoinedMatches AS DECIMAL(10,4))
        ,	a.LeagueScore = a.LeagueScore + t.LeagueScore
        , 	a.TotalJoinedDays = a.TotalJoinedDays + 1
        , 	a.TotalJoinedMatches = a.TotalJoinedMatches + t.TotalJoinedMatches
        , 	a.TotalJoinedSuspiciousMatches = a.TotalJoinedSuspiciousMatches + t.TotalJoinedSuspiciousMatches
        ,	a.LastModifiedDate = @lv_CurrentDate
        ,	a.LastModifiedTime = @lv_CurrentDateTime
    WHERE t.IsNewCouple = 0;    
    
    /* Update Suspicious Info */
    INSERT INTO SPU_AIML.AssociationSuspiciousInfo(CustID1, CustID2, MatchIDList, BettypeList)
	SELECT 	t.CustID1
		, 	t.CustID2
        , 	t.MatchIDList
        , 	t.BettypeList
    FROM Temp_CoupleScores AS t
    WHERE IsNewCouple = 1;
    
    UPDATE SPU_AIML.AssociationSuspiciousInfo AS a
		INNER JOIN Temp_CoupleScores AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	a.MatchIDList = CONCAT(a.MatchIDList,',', t.MatchIDList)
        ,	a.BettypeList = CONCAT(a.BettypeList,',', t.BettypeList)
    WHERE t.IsNewCouple = 0;
        
	/* Remove garbage */
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleMajorLeague;
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleMinorLeague;
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleGini;
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleScores;
     
END