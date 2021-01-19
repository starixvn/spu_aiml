CREATE TABLE `AssociationStatsStaging` (
  `ID` bigint unsigned NOT NULL AUTO_INCREMENT,
  `CustID1` bigint unsigned NOT NULL,
  `CustID2` bigint unsigned NOT NULL,
  `TimeScore` decimal(10,4) unsigned NOT NULL,
  `MatchID` bigint unsigned NOT NULL,
  `Bettype` int unsigned NOT NULL,
  `LeagueID` bigint unsigned NOT NULL,
  `IsMajorLeague` bit(1) DEFAULT NULL,
  `TotalJoinningCombs` int unsigned NOT NULL,
  PRIMARY KEY (`ID`),
  INDEX `IX_AssociationStatsStaging_CustID1CustID2` (`CustID1`,`CustID2`),
  INDEX `IX_AssociationStatsStaging_MatchIDBettype` (`MatchID`,`Bettype`),
  INDEX `IX_AssociationStatsStaging_IsMajorLeague` (`IsMajorLeague`)
) ENGINE=InnoDB;
