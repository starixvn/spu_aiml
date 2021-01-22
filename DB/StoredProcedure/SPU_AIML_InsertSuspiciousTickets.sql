CREATE DEFINER=`aimlOwner`@`%` PROCEDURE `SPU_AIML_InsertSuspiciousTickets`(
	IN 	ip_SuspiciousTickets 	JSON,
    
    OUT op_ErrorMessage 		VARCHAR(200)
)
    SQL SECURITY INVOKER
BEGIN
	/*
		Created:	20201204@Long.Luu
		Task:		Insert Suspicious Ticket [Redmine ID: #0000]
		DB:			SPU_AIML
		Original: 

		Revisions:
			- 20201204@Long.Luu: Created [Redmine ID: #0000]
            
		Example:
			call SPU_AIML.SPU_AIML_InsertSuspiciousTickets
				('[{"Trans": 43600693, "C": 22091984, "M": 1222, "Usn2": "test", "TD": "2020-12-12", "WLD": "2020-12-12", "OS": 8, "O": 0.9, "Hdp1": 2, "Hdp2": 0, "Stake": 100, "S": "WON", "SID": 113, "WL": 190, "AS": 100, "AR": 1,"LHS": 1, "LAS": 0, "LI": 1, "BT": 1, "BC": "a", "BF": "m", "RA": 23343, "RM": 24141', "RS": 1222,"Cur": 22, "IP": "10.18.200.70", "Balance": 2209.1984},{..}]');    
	*/ 

    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN         
        GET DIAGNOSTICS CONDITION 1 op_ErrorMessage = MESSAGE_TEXT;
    END;
            
    INSERT INTO SPU_AIML.SuspiciousTickets(TransID, CustID, MatchID, Username2, TransDate, WinlostDate, OddsSpread, Odds, Hdp1, Hdp2,
		Stake, Status, StatusID, WinLost, ActualStake, ActualRate, LiveHomeScore, LiveAwayScore, LiveIndicator, 
        BetType, BetTeam, BetFrom, ARecommend, MRecommend, SRecommend, Currency, IP, Balance)
	SELECT 	tmpTable.TransID
		, 	tmpTable.CustID
		, 	tmpTable.MatchID
        , 	tmpTable.Username2
        , 	tmpTable.TransDate
        , 	tmpTable.WinlostDate
        , 	tmpTable.OddsSpread
        , 	tmpTable.Odds
        , 	tmpTable.Hdp1
        , 	tmpTable.Hdp2
        , 	tmpTable.Stake
        , 	tmpTable.Status
        , 	tmpTable.StatusID
        , 	tmpTable.WinLost
        , 	tmpTable.ActualStake
        , 	tmpTable.ActualRate
        , 	tmpTable.LiveHomeScore
        , 	tmpTable.LiveAwayScore
        , 	tmpTable.LiveIndicator
        , 	tmpTable.BetType
        , 	tmpTable.BetTeam
        , 	tmpTable.BetFrom
        , 	tmpTable.ARecommend
        , 	tmpTable.MRecommend
        , 	tmpTable.SRecommend
        , 	tmpTable.Currency
        , 	tmpTable.IP
        , 	tmpTable.Balance        
	FROM JSON_TABLE(ip_SuspiciousTickets,
		 "$[*]" COLUMNS(
			  TransID 			BIGINT UNSIGNED		PATH "$.Trans"
			, CustID			INT UNSIGNED		PATH "$.C"
			, MatchID			INT UNSIGNED		PATH "$.M"
            , Username2			NVARCHAR(50)		PATH "$.Usn2"
            , TransDate			DATETIME			PATH "$.TD"
            , WinlostDate		DATE				PATH "$.WLD"
			, OddsSpread		DECIMAL(6,3)		PATH "$.OS"
			, Odds				DECIMAL(8,3)		PATH "$.O"
            , Hdp1				DECIMAL(6,3)		PATH "$.Hdp1"
            , Hdp2				DECIMAL(6,3)		PATH "$.Hdp2"
            , Stake				DECIMAL(20,4)		PATH "$.Stake"
			, Status			NVARCHAR(10)		PATH "$.S"
			, StatusID			TINYINT				PATH "$.SID"
            , WinLost			DECIMAL(20,4)		PATH "$.WL"
            , ActualStake		DECIMAL(20,4)		PATH "$.AS"
            , ActualRate		DECIMAL(10,4)		PATH "$.AR"
			, LiveHomeScore		SMALLINT			PATH "$.LHS"
			, LiveAwayScore		SMALLINT			PATH "$.LAS"
            , LiveIndicator		BIT					PATH "$.LI"
            , BetType			SMALLINT			PATH "$.BT"
            , BetTeam			NVARCHAR(10)		PATH "$.BC"
			, BetFrom			NVARCHAR(1)			PATH "$.BF"
			, ARecommend		INT UNSIGNED		PATH "$.RA"
            , MRecommend		INT UNSIGNED		PATH "$.RM"
            , SRecommend		INT UNSIGNED		PATH "$.RS"
            , Currency			SMALLINT UNSIGNED	PATH "$.Cur"
			, IP				NVARCHAR(15)		PATH "$.IP"
            , Balance			DECIMAL(20,4)		PATH "$.Balance"
		 )) AS tmpTable;      
     
END