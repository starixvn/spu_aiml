CREATE TABLE `AssociationSuspiciousInfo` (
  `ID` bigint unsigned NOT NULL AUTO_INCREMENT,
  `CustID1` bigint unsigned NOT NULL,
  `CustID2` bigint unsigned NOT NULL,
  `MatchIDList` varchar(8000) COLLATE utf8_unicode_ci NOT NULL,
  `BettypeList` varchar(8000) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`ID`),
  INDEX `IX_AssociationSuspiciousInfo_CustID1CustID2` (`CustID1`,`CustID2`)
) ENGINE=InnoDB;
