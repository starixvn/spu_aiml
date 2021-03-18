from itertools import combinations,islice
from multiprocessing import Pool
from tqdm import tqdm
from scipy.special import comb
from numba import njit



@njit
def compute_prob():
  ls = [i for i in range(1,81)]
  combs = combinations(ls,20)
  R210_to_695 = 0
  R696_to_763 = 0
  R764_to_855 = 0
  R856_to_923 = 0
  R924_to_1410 = 0
  # ii = 0
  
  for kk in combs:
    summation = sum(kk)
    if summation>=210 and summation<=695:
      R210_to_695 += 1
    elif summation>=696 and summation<=763:
      R696_to_763 += 1
    elif summation>=764 and summation<=855:
      R764_to_855 += 1
    elif summation>=856 and summation<=923:
      R856_to_923 += 1
    else:
      R924_to_1410 += 1
    # if ii != 0 and ii % 1000000 == 0:
    #   print('*************************************************')
    #   print(f'{ii}/{num_comb} has been computed successfully !')
    #   print(f"Proba R210_to_695 {R210_to_695/num_comb}",
    #         f"Proba R696_to_763 {R696_to_763/num_comb}",
    #         f"Proba R764_to_855 {R764_to_855/num_comb}",
    #         f"Proba R856_to_923 {R856_to_923/num_comb}",
    #         f"Proba R924_to_1410 {R924_to_1410/num_comb}",
    #         sep='\n')
    # ii += 1
  return R210_to_695,R696_to_763,R764_to_855,R856_to_923,R924_to_1410

if __name__=='__main__':

  num_comb = comb(80,20)
  a,b,c,d,e = compute_prob()
  print('*************************************************')
  # print(f'{ii}/{num_comb} has been computed successfully !')
  print(f"Proba R210_to_695 {a/num_comb}",
        f"Proba R696_to_763 {b/num_comb}",
        f"Proba R764_to_855 {c/num_comb}",
        f"Proba R856_to_923 {d/num_comb}",
        f"Proba R924_to_1410 {e/num_comb}",
        sep='\n')

for (nthdraw in 2:draws){
  print("*************************************************************")
  for (thisdraw in nthdraw:(balls-draws+nthdraw )){
    partitions[, thisdraw] <- 
      c(rep(0, thisdraw), cumpartitions[1:(maxsum-thisdraw), thisdraw-1])
      print(partitions) 
    }
    
  partitions[, 1:(nthdraw-1)] <- 0
  print(partitions)  
  cumpartitions <- rowCumsums(partitions)
  print(cumpartitions)
  }