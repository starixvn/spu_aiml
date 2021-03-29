DROP TABLE IF EXISTS `SPU_AIML`.`CoupleDailyStats`;
CREATE TABLE `SPU_AIML`.`CoupleDailyStats` (
  `CustID1` 					bigint unsigned NOT NULL,
  `CustID2` 					bigint unsigned NOT NULL,
  `TimeInterval` 				decimal(10,4) NOT NULL,
  `TotalJoiningCombs` 			int NOT NULL,
  `TotalJoiningSuspiciousCombs` int NOT NULL,
  `LeagueScore` 				decimal(10,4) NOT NULL,
  PRIMARY KEY (`CustID1`,`CustID2`)
) ENGINE=InnoDB;
