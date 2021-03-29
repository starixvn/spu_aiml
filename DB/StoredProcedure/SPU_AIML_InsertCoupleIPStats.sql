DELIMITER $$
DROP PROCEDURE IF EXISTS `SPU_AIML_InsertCoupleIPStats`;

CREATE PROCEDURE `SPU_AIML_InsertCoupleIPStats`(
	IN 	ip_CoupleIPStats 		JSON,
    
    OUT op_ErrorMessage 		VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20210315@Long.Luu
		Task:		Insert Couple IP Stats [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20210315@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertCoupleIPStats ('[{"C1": 1, "C2": 1111, "M": 1, "H": 1, "A": 1, "L": 1, "ED": "2021-03-14 00:00:000", "BT": "1,3,7,8", "BTC": 4, "IP": "127.0.0.1,10.40.40.90,10.40.40.99", "IPC": 3}]', @msg);    
	*/ 

    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;  
    
    DROP TEMPORARY TABLE IF EXISTS Temp_IPAssociation;
    CREATE TEMPORARY TABLE Temp_IPAssociation (
		CustID1 			BIGINT UNSIGNED NOT NULL,
		CustID2 			BIGINT UNSIGNED NOT NULL,
        IsNewCouple			BIT DEFAULT 1,
		PRIMARY KEY (CustID1,CustID2),
        INDEX IX_Temp_IPAssociation_IsNewCouple(IsNewCouple)
	);
    
    DROP TEMPORARY TABLE IF EXISTS Temp_CoupleIPStats;
    CREATE TEMPORARY TABLE Temp_CoupleIPStats (
		CustID1 		BIGINT UNSIGNED NOT NULL,
		CustID2 		BIGINT UNSIGNED NOT NULL,
		MatchID 		BIGINT UNSIGNED NOT NULL,
		HomeID 			INT UNSIGNED NOT NULL,
		AwayID 			INT UNSIGNED NOT NULL,
		LeagueID 		INT UNSIGNED NOT NULL,
		EventDate 		DATETIME NOT NULL,
		BettypeList		VARCHAR(200) NOT NULL,
		BettypeCount 	SMALLINT UNSIGNED NOT NULL,
		IP 				VARCHAR(1000) NOT NULL,
		IPCount 		SMALLINT UNSIGNED NOT NULL,
		PRIMARY KEY (CustID1,CustID2)
	);
    
    INSERT INTO Temp_CoupleIPStats(CustID1, CustID2, MatchID, HomeID, AwayID, LeagueID, EventDate, BettypeList, BettypeCount, IP, IPCount)
	SELECT 	tmpTable.CustID1
		, 	tmpTable.CustID2
		, 	tmpTable.MatchID
        , 	tmpTable.HomeID
        , 	tmpTable.AwayID
        , 	tmpTable.LeagueID
        , 	tmpTable.EventDate
        , 	tmpTable.BettypeList
        ,	tmpTable.BettypeCount
        , 	tmpTable.IP
        , 	tmpTable.IPCount
	FROM JSON_TABLE(ip_CoupleIPStats,
		 "$[*]" COLUMNS(
			  CustID1 				BIGINT UNSIGNED		PATH "$.C1"
			, CustID2				BIGINT UNSIGNED		PATH "$.C2"
			, MatchID				BIGINT UNSIGNED		PATH "$.M"
            , HomeID				BIGINT UNSIGNED		PATH "$.H"
            , AwayID				BIGINT UNSIGNED		PATH "$.A"
            , LeagueID				BIGINT UNSIGNED		PATH "$.L"
            , EventDate				DATE				PATH "$.ED"
            , BettypeList			VARCHAR(200)		PATH "$.BT"
            , BettypeCount			SMALLINT UNSIGNED	PATH "$.BTC"
            , IP					VARCHAR(1000)		PATH "$.IP"
            , IPCount				SMALLINT UNSIGNED	PATH "$.IPC"
		 )) AS tmpTable;  
     
    INSERT INTO SPU_AIML.CoupleIPStats(CustID1, CustID2, MatchID, HomeID, AwayID, LeagueID, EventDate, BettypeList, BettypeCount, IP, IPCount)
	SELECT 	t.CustID1
		, 	t.CustID2
		, 	t.MatchID
        , 	t.HomeID
        , 	t.AwayID
        , 	t.LeagueID
        , 	t.EventDate
        , 	t.BettypeList
        ,	t.BettypeCount
        , 	t.IP
        , 	t.IPCount
	FROM Temp_CoupleIPStats AS t;
        
	INSERT INTO Temp_IPAssociation(CustID1, CustID2)
	SELECT 	s.CustID1
		, 	s.CustID2
	FROM SPU_AIML.CoupleIPStats AS s
		INNER JOIN (
			SELECT DISTINCT CustID1, CustID2
			FROM Temp_CoupleIPStats
		) AS t ON t.CustID1 = s.CustID1 AND t.CustID2 = s.CustID2
	GROUP BY s.CustID1, s.CustID2
	HAVING SUM(s.BettypeCount) >= 10;
    
    UPDATE Temp_IPAssociation AS t
		LEFT JOIN SPU_AIML.AssociationByIP AS a ON t.CustID1 = a.CustID1 AND t.CustID2 = a.CustID2
	SET t.IsNewCouple = 0
	WHERE a.CustID1 IS NOT NULL
		AND a.CustID2 IS NOT NULL;
        
	INSERT INTO SPU_AIML.AssociationByIP(CustID1, CustID2, CreatedDate, CreatedTime)
    SELECT 	CustID1
		, 	CustID2
        ,	CURRENT_DATE()
        ,	CURRENT_DATE()
    FROM Temp_IPAssociation
    WHERE IsNewCouple = 1;
    
    SELECT 	CustID1
		, 	CustID2
    FROM Temp_IPAssociation
    WHERE IsNewCouple = 1;
END$$