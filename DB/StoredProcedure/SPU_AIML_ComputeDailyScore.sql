
DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_ComputeDailyScore`$$

CREATE DEFINER=`AIMLOwner`@`%` PROCEDURE `SPU_AIML_ComputeDailyScore`(
	IN 	ip_ScanDate				DATETIME,
    
    OUT op_ErrorMessage 		VARCHAR(200)
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
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleScores;
	CREATE TEMPORARY TABLE Temp_CoupleScores (
			CustID1			BIGINT UNSIGNED
		,	CustID2			BIGINT UNSIGNED
		,	Score			SMALLINT UNSIGNED
		,	PRIMARY KEY 	PK_Temp_CoupleScores(CustID1,CustID2)
	);
    
    /* Compute Accummalted score SCORE */
    INSERT INTO Temp_CoupleScores(CustID1, CustID2, Score)
    SELECT 	CustID1
		, 	CustID2
		,	(TimeScore + MatchScore * LeagueScore) / (TotalJoiningDays * 2) * 100
    FROM SPU_AIML.AssociationStats
    WHERE LastModifiedDate = ip_ScanDate;
    
    /* Update Association Stats */
	INSERT IGNORE INTO SPU_AIML.AssociationByAI(CustID1, CustID2, Score, LastModifiedDate)
	SELECT 	t.CustID1
		, 	t.CustID2
        , 	t.Score
        , 	ip_ScanDate
    FROM Temp_CoupleScores AS t;
    
    UPDATE SPU_AIML.AssociationByAI AS a
		INNER JOIN Temp_CoupleScores AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	a.Score = t.Score
        ,	a.LastModifiedDate = ip_ScanDate;
    
	/* Remove garbage */
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleScores;
   
	UPDATE SPU_AIML.SystemParameter
    SET ParameterValue = ip_ScannedDateTime
	WHERE ParameterID = 1;
END$$