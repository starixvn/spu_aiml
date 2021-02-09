DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_ExtractDailyAssociation`;
CREATE DEFINER=`AIMLOwner`@`%` PROCEDURE `SPU_AIML_ExtractDailyAssociation`(
	IN 	ip_ScanDate				DATETIME,
    
    OUT op_ErrorMessage 		VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210115@Long.Luu
		Task:		Extract Daily Association [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210115@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_ExtractDailyAssociation();  
	*/ 
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
    INSERT IGNORE INTO SPU_AIML.AssociationByAI(CustID1, CustID2, CreatedDate)
	SELECT 	t.CustID1
		, 	t.CustID2
        , 	ip_ScanDate
    FROM DailyScore AS t
    WHERE t.Score >= 50;
END$$