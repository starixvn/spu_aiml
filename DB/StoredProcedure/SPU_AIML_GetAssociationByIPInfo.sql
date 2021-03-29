DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_GetAssociationByIPInfo`;
CREATE DEFINER=`AIMLOwner`@`%` PROCEDURE `SPU_AIML_GetAssociationByIPInfo`(
	IN 	ip_CustID1 			BIGINT UNSIGNED,
    IN 	ip_CustID2 			BIGINT UNSIGNED,
    
    OUT op_TotalMatchCount 	INT UNSIGNED,
    OUT op_TotalIPCount 	INT UNSIGNED,
	OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210317@Long.Luu
		Task:		Get Association by IP Info of a couple [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210317@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_GetAssociationInfo(1,1000,@resultsMessage,@totalMatchCount);    
	*/
    DECLARE lv_MatchIDList 		VARCHAR(8000);
    DECLARE lv_BettypeIDList 	VARCHAR(8000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;	
    
	DROP TEMPORARY TABLE IF EXISTS Temp_Match;    
	CREATE TEMPORARY TABLE Temp_Match 
    (	 
			ID				BIGINT UNSIGNED	NOT NULL AUTO_INCREMENT PRIMARY KEY
		, 	MatchID			BIGINT UNSIGNED NOT NULL
        , 	INDEX		    IX_Temp_Match(MatchID) 
    );  
        
    IF EXISTS(SELECT 1 FROM SPU_AIML.CoupleIPStats WHERE CustID1 = ip_CustID1 AND CustID2 = ip_CustID2) THEN		
		INSERT INTO Temp_Match(MatchID)
        SELECT MatchID
        FROM SPU_AIML.CoupleIPStats
		WHERE CustID1 = ip_CustID1 AND CustID2 = ip_CustID2
        ORDER BY ID DESC
        LIMIT 50;
   
		SELECT 	s.MatchID, s.HomeID, s.AwayID, s.LeagueID, s.EventDate
			,	s.BettypeList
            ,	s.IP 
        FROM SPU_AIML.CoupleIPStats AS s
			INNER JOIN Temp_Match AS m ON s.MatchID = m.MatchID
		WHERE s.CustID1 = ip_CustID1 AND s.CustID2 = ip_CustID2;
		
		SELECT COUNT(MatchID)
		INTO op_TotalMatchCount
		FROM SPU_AIML.CoupleIPStats AS s
		WHERE s.CustID1 = ip_CustID1 AND s.CustID2 = ip_CustID2;
        
        SELECT SUM(IPCount)
		INTO op_TotalIPCount
		FROM SPU_AIML.CoupleIPStats
		WHERE CustID1 = ip_CustID1 AND CustID2 = ip_CustID2;
    ELSE
		SET op_TotalMatchCount = 0;
        SET op_TotalIPCount = 0;
    END IF;
    
END$$