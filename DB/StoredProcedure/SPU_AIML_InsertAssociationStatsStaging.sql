DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_InsertAssociationStatsStaging`;

CREATE DEFINER=`AIMLOwner`@`%` PROCEDURE `SPU_AIML_InsertAssociationStatsStaging`(
	IN 	ip_StatsStaging 	JSON,
    
	OUT op_ErrorMessage 	VARCHAR(200)
)
BEGIN
	/*
		Created:	20200112@Darius.Nguyen
		Task:		Insert Association Stats Staging [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20200112@Darius.Nguyen: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertAssociationStatsStaging('[{"C1": 1572, "C2": 2572, "TS": 0.5, "M": 1, "B": 1, "L": 1, "TJC": 2, "IML": "1", "IN": "1"}]', @msg);    
            select @msg;
	*/
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;

	INSERT INTO SPU_AIML.AssociationStatsStaging(CustID1, CustID2, TimeScore, MatchID, Bettype, LeagueID, TotalJoiningCombs, IsMajorLeague, IsNewData)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
		, 	tmpTable.TimeScore
        , 	tmpTable.MatchID
        , 	tmpTable.Bettype     
		,	tmpTable.LeagueID
        ,	tmpTable.TotalJoinningCombs
        ,	tmpTable.IsMajorLeague
        ,	tmpTable.IsNewData
	FROM JSON_TABLE(ip_StatsStaging,
		 "$[*]" COLUMNS(
			  CustID1 				BIGINT UNSIGNED				PATH "$.C1"
			, CustID2				BIGINT UNSIGNED				PATH "$.C2"
			, TimeScore				DECIMAL(10,4)				PATH "$.TS"
            , MatchID				BIGINT UNSIGNED				PATH "$.M"
            , Bettype				INT UNSIGNED				PATH "$.B"
            , LeagueID				BIGINT UNSIGNED				PATH "$.L"
            , TotalJoinningCombs	INT UNSIGNED				PATH "$.TJC"
            , IsMajorLeague			BIT							PATH "$.IML"
            , IsNewData				BIT							PATH "$.IN"
		 )) AS tmpTable;      
     
END $$