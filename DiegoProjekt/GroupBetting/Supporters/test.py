# import os
from tqdm import tqdm
if __name__ == "__main__":
    # path = "/home/vndata4ai/Data4AI_minute/"
    # backup = "/home/vnteam/Data/MatchData/BackUp/"
    # for fn in os.listdir(path):
    #     if fn.startswith('bettrans_03_26'):
    #         os.rename(path+fn,backup+fn)
    # ls = [i for i in tqdm(range(10000000),desc='Fuck Progress')]
    # print('Diego awesome !')
    while True:
        try:
            x = int(input("Please enter a number: "))
            # break
            print('Module !')
        except ValueError:
        # except TabError:
            print("Oops!  That was no valid number.  Try again...")
            raise ValueError
            # raise
            # raise NameError
        print('Apprentice')