import pandas as pd
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed

def square(x):
    return x**2
        


if __name__ == "__main__":
    ls=[x for x in range(10)]
    with ProcessPoolExecutor() as executor:
        results=[executor.submit(square,x) for x in ls]

        for f in as_completed(results):
            print(f.result())

    