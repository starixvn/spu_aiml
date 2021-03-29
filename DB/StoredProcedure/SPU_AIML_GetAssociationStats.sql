USE SPU_AIML;
DROP PROCEDURE IF EXISTS `SPU_AIML_GetAssociationStats`;

DELIMITER $$
CREATE DEFINER=`AIMLOwner`@`%` PROCEDURE `SPU_AIML_GetAssociationStats`(
	IN 	ip_FromCustID1 		BIGINT UNSIGNED,
    IN 	ip_ToCustID1 		BIGINT UNSIGNED,
    
	OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210126@Long.Luu
		Task:		Get data from Association Stats Staging [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210126@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_GetAssociationStats(1,1000,@resultsMessage);    
	*/
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;

	DROP TEMPORARY TABLE IF EXISTS Temp_AssociationStats;    
	CREATE TEMPORARY TABLE Temp_AssociationStats 
    (	 
			CustID1					BIGINT UNSIGNED	NOT NULL
		, 	CustID2					BIGINT UNSIGNED NOT NULL
		, 	TimeScore				DECIMAL(10,4) NOT NULL
		, 	MatchID					BIGINT UNSIGNED
		, 	Bettype					INT UNSIGNED
		, 	LeagueID				BIGINT UNSIGNED
		, 	IsMajorLeague			BIT
		, 	TotalJoiningCombs		INT UNSIGNED        
        , 	IsNewData				BIT
		, 	AccTimeScore			DECIMAL(10,4) DEFAULT 0
		, 	AccMatchScore			DECIMAL(10,4) DEFAULT 0
		, 	AccLeagueScore			DECIMAL(10,4) DEFAULT 0
        ,	AccTotalJoiningDays		INT UNSIGNED  DEFAULT 0
        , 	INDEX		    		IX_Temp_AssociationStats_CustID1_CustID2(CustID1,CustID2) 
    );     
    
    INSERT INTO Temp_AssociationStats(CustID1, CustID2, TimeScore, MatchID, Bettype, LeagueID, IsMajorLeague, TotalJoiningCombs, IsNewData)
	SELECT CustID1, CustID2, TimeScore, MatchID, Bettype, LeagueID, IsMajorLeague, TotalJoiningCombs, IsNewData
    FROM SPU_AIML.AssociationStatsStaging
    WHERE CustID1 BETWEEN ip_FromCustID1 AND ip_ToCustID1;
    
    UPDATE Temp_AssociationStats AS t
		LEFT JOIN SPU_AIML.AssociationStats AS a ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	t.AccTimeScore =  a.TimeScore
		,	t.AccMatchScore =  a.MatchScore
        ,	t.AccLeagueScore =  a.LeagueScore
        ,	t.AccTotalJoiningDays = a.TotalJoiningDays;
     
     SELECT *
     FROM Temp_AssociationStats;
     
END$$