def compute_alpha(main_part,s,A,B):
  return main_part*(main_part*(1-main_part)/(s**2/(B-A)**2)-1)

def compute_beta(main_part,alpha):
  return alpha*(1-main_part)/main_part
  
if __name__ == "__main__":

  xbar=.851
  s=.056
  A=.645
  B=.947
  main_part=(xbar-A)/(B-A)
  alpha=compute_alpha(main_part,s,A,B)
  beta=compute_beta(main_part,3.546)
  print('alpha = %.3f , beta = %.3f' % (alpha,beta))
