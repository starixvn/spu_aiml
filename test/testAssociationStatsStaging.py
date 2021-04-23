from DataAccess.GroupBettingDA.SPU_AIML.AssociationStatsStaging import AssociationStatsStaging

association_stats_staging = AssociationStatsStaging()

association_stats_staging.truncate()
association_stats_staging.insert([[{"C2": 9, "C1": 8, "TS": 1.1, "M": 100, "B": 1, "L": 1, "TJC": 1, "IML": 1, "IN": 1}]])
association_stats_staging.insert([[{"C2": 19, "C1": 9, "TS": 1.1, "M": 100, "B": 1, "L": 1, "TJC": 1, "IML": 1, "IN": 1}]])
association_stats_staging.insert([[{"C2": 19, "C1": 10, "TS": 1.1, "M": 100, "B": 1, "L": 1, "TJC": 1, "IML": 1, "IN": 1}]])
result = association_stats_staging.get([8, 9, 10])
print(result)
association_stats_staging.update([8, 9, 10])
result = association_stats_staging.get([8, 9, 10])
print(result)
