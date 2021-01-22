CREATE DEFINER=`darius.vn`@`%` PROCEDURE `SPU_AIML_GetGroupByCouple`(
    IN	ip_BatchSize1				INT UNSIGNED,
    IN  ip_BatchSize2				INT UNSIGNED,
    
    OUT op_ErrorMessage 			VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210120@Darius.Nguyen
		Task:		Get New GroupBy Couple [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210120@Darius.Nguyen: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_GetGroupByCouple(1, 5000);    
	*/ 
    SELECT * FROM GroupByCouple
    LIMIT ip_Batchsize1, ip_BatchSize2;
     
END