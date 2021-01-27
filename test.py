import pandas as pd
import os
import pickle

root = "D:/Project/Formula_Bet/MatchData"
fn = "bettrans20201129.csv"
save_folder="D:/Project/Formula_Bet/SaveData"
save_fn='cus_list.pkl'

# ls=[(1,2,3),(4,5,6),(7,8,9)]

# print(f"DF {pd.DataFrame(ls,columns=['x','y','z'])}")

df=pd.read_csv(os.path.join(root,fn),encoding='ISO-8859-1')
# print(f"df {df.head()}")
# DATE = df[(df.bettype.isin([1,3,7,8]))&(df.liveindicator)]
# CUST_LIST=DATE.custid.unique()
# print(f"LEN CUST LIST {len(CUST_LIST)}")
# with open(os.path.join(save_folder,save_fn),'wb') as f:
#     pickle.dump(CUST_LIST,f)
live=df[df.liveindicator==1]
print(f"BETTYPE UNIQUE {df.bettype.unique()}")