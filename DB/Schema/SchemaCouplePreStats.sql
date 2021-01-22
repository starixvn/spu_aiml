CREATE TABLE `CouplePreStats` (
  `ID` bigint unsigned NOT NULL AUTO_INCREMENT,
  `CustID1` bigint unsigned NOT NULL,
  `CustID2` bigint unsigned NOT NULL,
  `TimeScore` decimal(10,4) NOT NULL,
  `TotalJoinedSuspiciousMatches` INT NOT NULL,
  `TotalJoinedMatches` INT NOT NULL,
  `MatchIDList` varchar(8000) DEFAULT NULL,
  `BettypeList` varchar(8000) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  INDEX `IX_CouplePreStats_CustID1CustID2` (`CustID1`,`CustID2`)
) ENGINE=InnoDB;
