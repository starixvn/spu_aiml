CREATE TABLE `AssociationByAI` (
  `CustID1` 			bigint unsigned NOT NULL,
  `CustID2` 			bigint unsigned NOT NULL,
  `TimeScore` 			decimal(10,4) NOT NULL,
  `MatchScore` 			decimal(10,4) NOT NULL,
  `LeagueScore` 		decimal(10,4) NOT NULL,
  `Score` 				SMALLINT UNSIGNED NOT NULL,
  `TotalJoiningDays` 	int NOT NULL,
  `TotalJoiningCombs` 	int NOT NULL,
  `TotalJoiningSuspiciousCombs` int NOT NULL,
  `CreatedDate` 		date DEFAULT NULL,
  `CreatedTime` 		datetime DEFAULT NULL,
  PRIMARY KEY 	(`CustID1`,`CustID2`),
  KEY 			`IX_AssociationByAI_Score` (`Score`),
  KEY 			`IX_AssociationByAI_CreatedDate` (`CreatedDate`)
) ENGINE=InnoDB;
