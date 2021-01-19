CREATE PROCEDURE `SPU_AIML_InsertAssociationSuspiciousInfo`(
	IN 	ip_SuspiciousInfo 	JSON,
    
    OUT op_ErrorMessage 	VARCHAR(200)
)
BEGIN
	/*
		Created:	20200112@Darius.Nguyen
		Task:		Insert Association Suspicious Info [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20200112@Darius.Nguyen: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo
				('[{"C1": 1572, "C2": 2572, "ML": "2222,45", "TL": "3,3"}]');    
	*/

    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
     
    DROP TEMPORARY TABLE IF EXISTS Temp_SuspiciousInfo;    
	CREATE TEMPORARY TABLE Temp_SuspiciousInfo 
    (	 
			CustID1					BIGINT UNSIGNED	NOT NULL
		, 	CustID2					BIGINT UNSIGNED NOT NULL
        , 	MatchIDList				VARCHAR(2000) DEFAULT NULL
		, 	TransIdList				VARCHAR(2000) DEFAULT NULL
        ,	IsNewCouple	 			BIT DEFAULT 1
        , 	PRIMARY KEY	    		PK_Temp_SuspiciousInfo_CustID1_CustID2(CustID1,CustID2) 
        , 	INDEX	    			IX_Temp_SuspiciousInfo_IsNewCouple(IsNewCouple) 
    );      
            
    INSERT INTO Temp_SuspiciousInfo(CustID1, CustID2, MatchIDList, TransIDList)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
		, 	tmpTable.MatchIDList
        , 	tmpTable.TransIDList
	FROM JSON_TABLE(ip_SuspiciousInfo,
		 "$[*]" COLUMNS(
			  CustID1 						BIGINT UNSIGNED		PATH "$.C1"
			, CustID2						BIGINT UNSIGNED		PATH "$.C2"
			, MatchIDList					VARCHAR(2000)		PATH "$.ML"
            , TransIDList					VARCHAR(2000)		PATH "$.TL"
		 )) AS tmpTable;      
    
    UPDATE Temp_SuspiciousInfo AS t
		LEFT JOIN SPU_AIML.AssociationSuspiciousInfo AS a ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
	SET t.IsNewCouple = 0
    WHERE a.CustID1 IS NOT NULL
		AND a.CustID2 IS NOT NULL;
    
	INSERT INTO SPU_AIML.AssociationSuspiciousInfo(CustID1, CustID2, MatchIDList, TransIDList)
	SELECT 	t.CustID1
		, 	t.CustID2
        , 	t.MatchIDList
        , 	t.TransIDList
    FROM Temp_SuspiciousInfo AS t
    WHERE IsNewCouple = 1;
    
    UPDATE SPU_AIML.AssociationSuspiciousInfo AS a
		INNER JOIN Temp_SuspiciousInfo AS t ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
    SET 	a.MatchIDList = CONCAT(a.MatchIDList,',', t.MatchIDList)
        ,	a.TransIDList = CONCAT(a.TransIDList,',', t.TransIDList)
    WHERE t.IsNewCouple = 0;
    
    DROP TEMPORARY TABLE IF EXISTS Temp_SuspiciousInfo;
     
END