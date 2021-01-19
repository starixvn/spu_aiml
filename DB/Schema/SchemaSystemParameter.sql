CREATE TABLE `SystemParameter` (
  `ParameterID` smallint unsigned NOT NULL,
  `ParameterName` varchar(50) DEFAULT NULL,
  `ParameterDesc` varchar(200) DEFAULT NULL,
  `ParameterDataType` varchar(50) DEFAULT NULL,
  `ParameterValue` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`ParameterID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
