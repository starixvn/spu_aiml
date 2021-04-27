from DataAccess.GroupBettingDA.AssociationStats import AssociationStats

association_stats = AssociationStats()
association_stats.insert([[{"C2": 9, "C1": 8, "TS": 1.1, "MS": 1.2, "LS": 1.3, "TJD": 1, "TJC": 1, "TJSC": 1, "BC": 1}]], '2015-06-28')
result = association_stats.get(8, 9)
print(result)
