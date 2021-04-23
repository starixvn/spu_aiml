from DataAccess.GroupBettingDA.SPU_AIML.AssociationSuspiciousInfo import InsertAssociationSuspiciousInfo

insert_association_by_aispu = InsertAssociationSuspiciousInfo()
insert_association_by_aispu.execute([[{"C2": 9, "C1": 8, "ML": "a", "BL": "a"}]])
