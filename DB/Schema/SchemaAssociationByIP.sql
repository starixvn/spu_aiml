DROP TABLE IF EXISTS `SPU_AIML`.`AssociationByIP`;
CREATE TABLE `SPU_AIML`.`AssociationByIP` (
  `CustID1` 			bigint unsigned NOT NULL,
  `CustID2` 			bigint unsigned NOT NULL,
  `CreatedDate` 		date DEFAULT NULL,
  `CreatedTime` 		datetime DEFAULT NULL,
  PRIMARY KEY 	(`CustID1`,`CustID2`),
  KEY 			`IX_AssociationByIP_CreatedDate` (`CreatedDate`)
) ENGINE=InnoDB;
