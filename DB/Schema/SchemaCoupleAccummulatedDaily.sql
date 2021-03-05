DROP TABLE IF EXISTS `CoupleAccumulatedDaily`;

CREATE TABLE `CoupleAccumulatedDaily` (
  `CustID1` 					BIGINT UNSIGNED NOT NULL,
  `CustID2` 					BIGINT UNSIGNED NOT NULL,
  `TotalTimeInterval` 			BIGINT UNSIGNED NOT NULL,
  `TotalJoiningCombs` 			INT UNSIGNED NOT NULL,
  `TotalJoiningSuspiciousCombs` INT UNSIGNED NOT NULL,
  `MajorLeagueFrequency`		VARCHAR(8000) NOT NULL,
  `MinorLeagueFrequency`		VARCHAR(8000) NOT NULL,
  PRIMARY KEY (`CustID1`,`CustID2`)
) ENGINE=InnoDB;