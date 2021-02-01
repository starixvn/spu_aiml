CREATE TABLE `AssociationByAI` (
  `CustID1` bigint unsigned NOT NULL,
  `CustID2` bigint unsigned NOT NULL,
  `Score` decimal(10,6) NOT NULL,
  `LastModifiedDate` date DEFAULT NULL,
  `IsConfirmed` bit(1) DEFAULT b'0',
  `ScoreInt` smallint unsigned DEFAULT NULL,
  PRIMARY KEY (`CustID1`,`CustID2`),
  KEY `IX_AssociationByAI_LastModifiedDate` (`LastModifiedDate`),
  KEY `IX_AssociationByAI_IsConfirmed` (`IsConfirmed`)
) ENGINE=InnoDB;
