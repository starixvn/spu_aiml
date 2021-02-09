USE SPU_AIML;
DROP PROCEDURE IF EXISTS `SPU_AIML_InsertAssociationByAI`;

DELIMITER $$
CREATE DEFINER=`aimlOwner`@`%` PROCEDURE `SPU_AIML_InsertAssociationByAI`(
	IN 	ip_DailyStats 		JSON,
	IN 	ip_ScanDate			DATETIME,
    
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
			call SPU_AIML.SPU_AIML_InsertAssociationByAI ('[{"C1": 43600693, "C2": 45}]', '2021-01-11', @ErrorMessage);    
	*/ 
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
    
	INSERT IGNORE INTO SPU_AIML.AssociationByAI(CustID1, CustID2, CreatedDate)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
        ,	ip_ScanDate
	FROM JSON_TABLE(ip_DailyStats,
		 "$[*]" COLUMNS(
			  CustID1 		BIGINT UNSIGNED		PATH "$.C1"
			, CustID2		BIGINT UNSIGNED		PATH "$.C2"
		 )) AS tmpTable;  
     
END$$