#!/usr/bin/env python

from scipy.spatial.distance import pdist
from scipy.spatial.distance import squareform
import sys, os
import numpy as np

if __name__ == "__main__":
    
    d = np.loadtxt("top_models.dat", delimiter="\t")
    p = pdist(d, "cosine")
    np.save("top_models_similarity.npy", p, allow_pickle=False)