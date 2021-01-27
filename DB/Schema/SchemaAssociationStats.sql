CREATE TABLE `AssociationStats` (
  `ID` bigint unsigned NOT NULL AUTO_INCREMENT,
  `CustID1` bigint unsigned NOT NULL,
  `CustID2` bigint unsigned NOT NULL,
  `TimeScore` decimal(10,4) NOT NULL,
  `MatchScore` decimal(10,4) NOT NULL,
  `LeagueScore` decimal(10,4) NOT NULL,
  `TotalJoiningDays` int NOT NULL,
  `TotalJoiningCombs` int NOT NULL,
  `TotalJoiningSuspiciousCombs` int NOT NULL,
  `BetCount` bigint NOT NULL,
  `LastModifiedDate` date DEFAULT NULL,
  `LastModifiedTime` datetime DEFAULT NULL,
  `IsConfirmed` bit(1) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  INDEX `IX_AssociationStats_CustID1CustID2` (`CustID1`,`CustID2`),
  INDEX `IX_AssociationStats_LastModifiedDate` (`LastModifiedDate`),
  INDEX `IX_AssociationStats_IsConfirmed` (`IsConfirmed`)
) ENGINE=InnoDB;
