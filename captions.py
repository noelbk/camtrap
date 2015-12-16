#! /usr/bin/env python

import os
import random
import re
import sys

def load(lines):
    """load a bunch of captions and return an array of
    [([tops1], [bottoms1]), ([tops2], [bottoms2]), ...]

    lines that start with # are comments
    blank lines start a new ([tops2], [bottoms2]) set
    lines that start with writespace are bottoms
    else tops
    """
    captions = []
    tops = []
    bottoms = []
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            continue
            
        if not s:
            # start a new set of tops and bottoms
            if tops or bottoms:
                captions.append((tops, bottoms))
            tops = []
            bottoms = []
            continue

        if  re.match(r'^\s', line):
            bottoms.append(s)
        else:
            tops.append(s)

    if tops or bottoms:
        captions.append((tops, bottoms))

    return captions
    
        
def choose(captions):
    """choose a random (top, bottom) from the list returned by load()"""
    tops, bottoms = random.choice(captions)
    return random.choice(tops or ("",)), random.choice(bottoms or ("",))

def load_captions():
    """load("captions.txt")"""
    with open(os.path.join(os.path.dirname(__file__), "captions.txt")) as f:
        return load(f)
    
if __name__ == '__main__':
    print "\n".join(choose(load_captions()))
        
                 
