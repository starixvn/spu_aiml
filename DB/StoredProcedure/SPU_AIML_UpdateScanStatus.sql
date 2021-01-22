CREATE DEFINER=`aimlOwner`@`%` PROCEDURE `SPU_AIML_UpdateScanStatus`(
	IN 	ip_ScannedDateTime		DATETIME,
    
    OUT op_ErrorMessage 		VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20201204@Long.Luu
		Task:		Update scanning status [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20201204@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_GetAssociationStats(1, 5000);    
	*/ 
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
	UPDATE SPU_AIML.SystemParameter
    SET ParameterValue = ip_ScannedDateTime
	WHERE ParameterID = 1;
     
END