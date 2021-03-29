USE SPU_AIML;
DROP PROCEDURE IF EXISTS `SPU_AIML_InsertAssociationByAI`;

DELIMITER $$
CREATE DEFINER=`aimlOwner`@`%` PROCEDURE `SPU_AIML_InsertAssociationByAI`(
	IN 	ip_Association 		JSON,
    
    OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210217@Long.Luu
		Task:		Insert Association By AI [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210217@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertAssociationByAI ('[{"C1": 43600693, "C2": 45, "TS": 1, "MS": 1, "LS": 0.8, "S": 70, "TJD": 1, "TJC": 3, "TJSC": 2}]', @ErrorMessage);    
	*/ 
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
	INSERT IGNORE INTO SPU_AIML.AssociationByAI(CustID1, CustID2, TimeScore, MatchScore, LeagueScore, Score, TotalJoiningDays, TotalJoiningCombs, TotalJoiningSuspiciousCombs, CreatedDate, CreatedTime)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
		, 	tmpTable.TimeScore
        , 	tmpTable.MatchScore
        , 	tmpTable.LeagueScore
        , 	tmpTable.Score
        , 	tmpTable.TotalJoiningDays
        , 	tmpTable.TotalJoiningCombs
        , 	tmpTable.TotalJoiningSuspiciousCombs
        ,	NOW()
        ,	NOW()
	FROM JSON_TABLE(ip_Association,
		 "$[*]" COLUMNS(
			  CustID1 							BIGINT UNSIGNED		PATH "$.C1"
			, CustID2							BIGINT UNSIGNED		PATH "$.C2"
			, TimeScore							DECIMAL(10,4)		PATH "$.TS"
            , MatchScore						DECIMAL(10,4)		PATH "$.MS"
            , LeagueScore						DECIMAL(10,4)		PATH "$.LS"
            , Score								SMALLINT UNSIGNED	PATH "$.S"
            , TotalJoiningDays					SMALLINT			PATH "$.TJD"
            , TotalJoiningCombs					SMALLINT			PATH "$.TJC"
            , TotalJoiningSuspiciousCombs		SMALLINT			PATH "$.TJSC"
		 )) AS tmpTable;  
     
END$$