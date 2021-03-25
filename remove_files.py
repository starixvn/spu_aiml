from pathlib import Path
import glob
  

if __name__ == "__main__":

  root="/home/vndata4ai/Data4AI_minute/"
  # ls=[x for x in range(5,23)]
  for x in range(5,23):
    # for file in glob.glob(f"bettrans_03_24_2021_{str(x).zfill(2)}_*"):
    #   Path(file).unlink()
    print(f"bettrans_03_24_2021_{str(x).zfill(2)}_*")