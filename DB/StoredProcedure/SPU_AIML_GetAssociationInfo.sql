DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_GetAssociationInfo`;
CREATE DEFINER=`AIMLOwner`@`%` PROCEDURE `SPU_AIML_GetAssociationInfo`(
	IN 	ip_CustID1 			BIGINT UNSIGNED,
    IN 	ip_CustID2 			BIGINT UNSIGNED,
    
    OUT op_TotalMatchCount 	INT UNSIGNED,
	OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210304@Long.Luu
		Task:		Get Association Info of a couple [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210304@Long.Luu: Created [Redmine ID: #0000]
            
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
    
    DROP TEMPORARY TABLE IF EXISTS Temp_DistinctedMatch;    
	CREATE TEMPORARY TABLE Temp_DistinctedMatch 
    (	    
			ID				BIGINT UNSIGNED	NOT NULL AUTO_INCREMENT PRIMARY KEY
		, 	MatchID			BIGINT UNSIGNED NOT NULL
        , 	INDEX		    Temp_DistinctedMatch(MatchID) 
    );
    
    DROP TEMPORARY TABLE IF EXISTS Temp_Bettype;    
	CREATE TEMPORARY TABLE Temp_Bettype 
    (	 
			ID				BIGINT UNSIGNED	NOT NULL AUTO_INCREMENT PRIMARY KEY
		, 	BettypeID		SMALLINT UNSIGNED NOT NULL
    );  
        
    IF EXISTS(SELECT 1 FROM SPU_AIML.AssociationSuspiciousInfo WHERE CustID1 = ip_CustID1 AND CustID2 = ip_CustID2) THEN		
		SELECT MatchIDList, BettypeList
		INTO lv_MatchIDList, lv_BettypeIDList
		FROM SPU_AIML.AssociationSuspiciousInfo
		WHERE CustID1 = ip_CustID1 AND CustID2 = ip_CustID2;
    
		SET @sql = CONCAT("INSERT INTO Temp_Match (MatchID) VALUES ('", REPLACE(lv_MatchIDList, ",", "'),('"),"');");
		PREPARE stmt1 FROM @sql;
		EXECUTE stmt1;
		
		SET @sql = CONCAT("INSERT INTO Temp_Bettype (BettypeID) VALUES ('", REPLACE(lv_BettypeIDList, ",", "'),('"),"');");
		PREPARE stmt1 FROM @sql;
		EXECUTE stmt1;
		 
		SET @@sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));
		INSERT INTO Temp_DistinctedMatch(MatchID)
		SELECT DISTINCT MatchID
		FROM Temp_Match
		ORDER BY ID DESC;
		
		SELECT COUNT(1)
		INTO op_TotalMatchCount
		FROM Temp_DistinctedMatch;
		
		DELETE FROM Temp_DistinctedMatch
		WHERE ID > 50;
		
		WITH cts_matchbettype(MatchID,BettypeID) AS (
			SELECT DISTINCT m.MatchID, b.BettypeID
			FROM Temp_DistinctedMatch AS dm
				INNER JOIN Temp_Match AS m ON dm.MatchID = m.MatchID
				INNER JOIN Temp_Bettype AS b ON m.ID = b.ID
        )
		SELECT m.MatchID, GROUP_CONCAT(m.BettypeID) AS BettypeList
		FROM cts_matchbettype AS m
		GROUP BY m.MatchID;    
    ELSE
		SET op_TotalMatchCount = 0;
    END IF;
    
END$$