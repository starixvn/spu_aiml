DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_ExtractDailyAssociation`;

CREATE DEFINER=`AIMLOwner`@`%` PROCEDURE `SPU_AIML_ExtractDailyAssociation`(
	IN 	ip_BatchSize			BIGINT UNSIGNED,
    
    OUT op_ErrorMessage 		VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210317@Long.Luu
		Task:		Extract Daily Association [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210317@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_ExtractDailyAssociation();  
	*/ 
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_Couple;
    CREATE TEMPORARY TABLE Temp_Couple (
		CustID1 					BIGINT UNSIGNED NOT NULL,
		CustID2 					BIGINT UNSIGNED NOT NULL,
		PRIMARY KEY (`CustID1`,`CustID2`)
	);
    
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleDailyStats;
    CREATE TEMPORARY TABLE Temp_CoupleDailyStats (
		CustID1 					BIGINT UNSIGNED NOT NULL,
		CustID2 					BIGINT UNSIGNED NOT NULL,
		TimeInterval 				DECIMAL(10,4) NOT NULL,
		TotalJoiningCombs 			INT NOT NULL,
		TotalJoiningSuspiciousCombs INT NOT NULL,
        IsNewCouple					BIT DEFAULT 1,
		PRIMARY KEY (`CustID1`,`CustID2`)
	);

	IF EXISTS(SELECT 1 FROM SPU_AIML.CoupleDailyStats) THEN
		INSERT INTO Temp_Couple(CustID1, CustID2)
		SELECT 	DISTINCT CustID1, CustID2
		FROM SPU_AIML.CoupleDailyStats
		LIMIT ip_BatchSize;
		
		INSERT INTO Temp_CoupleDailyStats(CustID1, CustID2, TimeInterval, TotalJoiningCombs, TotalJoiningSuspiciousCombs)
		SELECT 	CustID1
			,	CustID2
			,	TimeInterval
			,	TotalJoiningCombs
			,	TotalJoiningSuspiciousCombs
		FROM SPU_AIML.CoupleDailyStats AS s
			INNER JOIN Temp_Couple AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2;
		
		UPDATE Temp_CoupleDailyStats AS t
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
			, 	1
			, 	t.TotalJoiningCombs
			, 	t.TotalJoiningSuspiciousCombs
			,	1
			,	ip_ScanDate
			,	lv_CurrentDateTime
		FROM Temp_CoupleDailyStats AS t
		WHERE IsNewCouple = 1;
		
		UPDATE SPU_AIML.AssociationStats AS a
			INNER JOIN Temp_CoupleDailyStats AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
		SET 	a.TimeScore = a.TimeScore + t.TimeScore
			,	a.MatchScore = a.MatchScore + t.MatchScore
			,	a.LeagueScore = a.LeagueScore + t.LeagueScore
			, 	a.TotalJoiningDays = t.TotalJoiningDays + 1
			, 	a.TotalJoiningCombs = a.TotalJoiningCombs + t.TotalJoiningCombs
			, 	a.TotalJoiningSuspiciousCombs = a.TotalJoiningSuspiciousCombs + t.TotalJoiningSuspiciousCombs
		WHERE t.IsNewCouple = 0;
		
		SELECT a.CustID1, a.CustID2
		FROM SPU_AIML.AssociationStats AS a
			INNER JOIN Temp_Couple AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
		WHERE a.TotalJoiningSuspiciousCombs >= 5
			AND ((a.TimeScore + a.MatchScore + a.LeagueScore) / (3 * a.TotalJoiningDays)) * 100 >= 70;
			
		DELETE s
		FROM SPU_AIML.CoupleDailyStats AS s
			INNER JOIN Temp_Couple AS t ON t.CustID1 = s.CustID1 AND t.CustID2 = s.CustID2;        
	ELSE
		SET op_ErrorMessage = 'DONE';
    END IF;
END$$