CREATE DEFINER=`darius.vn`@`%` PROCEDURE `SPU_AIML_GetCouplePreStats`(
    IN	ip_BatchSize1				BIGINT UNSIGNED,
    IN  ip_BatchSize2				BIGINT UNSIGNED,
    
    OUT op_ErrorMessage 			VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210120@Darius.Nguyen
		Task:		Get Data Couple Pre Stats [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210120@Darius.Nguyen: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_CouplePreStats(1, 5000);    
	*/ 
    SELECT 	CustID1
		,	CustID2
        ,	TimeScore
        ,	TotalJoinedSuspiciousMatches
        ,	TotalJoinedMatches
        ,	MatchIDList
        ,	BettypeList
	FROM SPU_AIML.CouplePreStats	
    LIMIT ip_Batchsize1, ip_BatchSize2;
     
END