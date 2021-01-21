import multiprocessing as mp
import time

#a=[i for i in range(100000)]
#b=[k for k in range(100000)]

def square_and_cub(args):
    print('\n',f'SQUARE a {args[0]**2} | CUBE b {args[1]**3}')

if __name__=='__main__':
    start=time.time()
    pool=mp.Pool(4)
    pool.map(square_and_cub,[x for x in zip([i for i in range(100000)],[k for k in range(100000)])])
    print('TOOK %.3f seconds' % (time.time()-start))