CREATE DEFINER=`CtsOwner`@`%` PROCEDURE `SPU_AIML_GetAssociationStatsStaging`(
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
			call SPU_AIML.SPU_AIML_GetAssociationStatsStaging(1,1000,@resultsMessage);    
	*/
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;

	SELECT CustID1, CustID2, TimeScore, MatchID, Bettype, LeagueID, IsMajorLeague, TotalJoiningCombs
    FROM SPU_AIML.AssociationStatsStaging
    WHERE CustID1 BETWEEN ip_FromCustID1 AND ip_ToCustID1;
     
END