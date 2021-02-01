import pandas as pd
import os
import pickle
import numpy as np
root = "D:/Project/Formula_Bet/MatchData"
fn = "bettrans20201129.csv"
save_folder="D:/Project/Formula_Bet/SaveData"
save_fn='cus_list.pkl'

# ls=[(1,2,3),(4,5,6),(7,8,9)]

# print(f"DF {pd.DataFrame(ls,columns=['x','y','z'])}")

# df=pd.read_csv(os.path.join(root,fn),encoding='ISO-8859-1')
# print(f"df {df.head()}")
# DATE = df[(df.bettype.isin([1,3,7,8]))&(df.liveindicator)]
# CUST_LIST=DATE.custid.unique()
# print(f"LEN CUST LIST {len(CUST_LIST)}")
# with open(os.path.join(save_folder,save_fn),'wb') as f:
#     pickle.dump(CUST_LIST,f)
# live=df[df.liveindicator==1]
# print(f"BETTYPE UNIQUE {df.bettype.unique()}")
# read customer list
# with open(os.path.join(save_folder,save_fn),'rb') as f:
#     CUST_LIST=pickle.load(f)

# build batches
# CUST_LIST=np.sort(CUST_LIST)
# BATCHES=[CUST_LIST[x:x+10] for x in range(0, len(CUST_LIST), 10)]
# print(f"BATCH 1st {BATCHES[0]}")
# print(f"MAX {np.max(BATCHES[0])}")
# print(f"MIN {np.min(BATCHES[0])}")

# def factorial(n):
#     '''returns n!'''
#     return 1 if n < 2 else n * factorial(n-1)

def tag(name, *content, cls=None, **attrs):
    """Generate one or more HTML tags"""
    if cls is not None:
        attrs['class'] = cls
    if attrs:
        attr_str = ''.join(' %s="%s"' % (attr, value) for attr, value in sorted(attrs.items()))
    else:
        attr_str = ''
    if content:
        return '\n'.join('<%s%s>%s</%s>' % (name, attr_str, c, name) for c in content)
    else:
        return '<%s%s />' % (name, attr_str)

if __name__ == "__main__":
    # print(tag('p', 'hello', id=33))
    # print(tag('p', 'hello', 'world', cls='sidebar'))
    # print(tag(content='testing', name="img"))
    my_tag = {'name': 'img', 'title': 'Sunset Boulevard','src': 'sunset.jpg', 'cls': 'framed'}
    print(tag(**my_tag))