CREATE TABLE `AssociationStatsStaging` (
  `ID` bigint unsigned NOT NULL AUTO_INCREMENT,
  `CustID1` bigint unsigned NOT NULL,
  `CustID2` bigint unsigned NOT NULL,
  `TimeScore` decimal(10,4) unsigned NOT NULL,
  `MatchID` bigint unsigned NOT NULL,
  `Bettype` int unsigned NOT NULL,
  `LeagueID` bigint unsigned NOT NULL,
  `IsMajorLeague` bit(1) DEFAULT NULL,
  `TotalJoiningCombs` int unsigned NOT NULL,
  `IsNewData` BIT NOT NULL DEFAULT 1,
  PRIMARY KEY (`ID`),
  INDEX `IX_AssociationStatsStaging_CustID1CustID2` (`CustID1`,`CustID2`),
  INDEX `IX_AssociationStatsStaging_IsNewData` (`IsNewData`)
) ENGINE=InnoDB;
