USE SPU_AIML;
DROP PROCEDURE IF EXISTS `SPU_AIML_UpdateAssociationStatsStagingStatus`;

DELIMITER $$
CREATE DEFINER=`AIMLOwner`@`%` PROCEDURE `SPU_AIML_UpdateAssociationStatsStagingStatus`(
	IN 	ip_FromCustID1 		BIGINT UNSIGNED,
    IN 	ip_ToCustID1 		BIGINT UNSIGNED,
    
	OUT op_ErrorMessage 	VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210318@Long.Luu
		Task:		Update IsNewData status of Association Stats Staging [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210318@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_UpdateAssociationStatsStagingStatus(1,1000,@resultsMessage);    
	*/
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
	UPDATE SPU_AIML.AssociationStatsStaging
    SET IsNewData = 0
    WHERE CustID1 BETWEEN ip_FromCustID1 AND ip_ToCustID1;
     
END$$