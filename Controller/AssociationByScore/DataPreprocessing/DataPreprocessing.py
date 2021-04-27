import logging
import os
import pickle
import re
import time

import pandas as pd
from tqdm import tqdm

from Configuration.Configuration import config
from Helper import Utilities

def run():
