import sys #handling arguments passed to function
import glob #file path handling
import os #checking files and writing to/from files
import re #regex matching
import numpy as np #for use in pyplot
import matplotlib.pyplot as pl #used to plot graphs
import multiprocessing as mp #drastic speedups when implemented on an i7-4700HQ
import heapq #to find n largest elements in makegraph

f1 = open("example.txt")

text = f1.read()

text = re.sub(r'(?m)^%+.*$','',text)
text = re.sub(r"(?m)([^\\])\%+.*?$",r'\1',text)
print(text)

exit()
f1 = open('1506/1506.07597.tex')

# lines = f1.readlines()
#
# outlines = []
#
# for x in lines:
#     if x[:1] == '%':
#         #print(x)
#         continue
#     else:
#         outlines.append(x)
# f1.seek(0)
otherlines = f1.read()
#print(otherlines)
otherlines = re.sub(r"(?m)[^\\]\%+.*?$|^%+.*$",'',otherlines)
otherlines = re.sub(r'\\begin\{comment\}.*?\\end\{comment\}','',otherlines,re.DOTALL)

cdelim = "CUSTOMDELIMITERHERE"

otherlines  = re.sub(r'\\begin\{equation\}|\\end\{equation\}|\\begin\{multline\}|\\end\{multline\}|\\begin\{gather\}|\\end\{gather\}|\\begin\{align\}|\\end\{align\}|\\begin\{flalign\*\}|\\end\{flalign\*\}|\\begin\{math\}|\\end\{math\}|[^\\]\\\[|\\\]|\$\$[^\^\_]',cdelim,otherlines)

#print(otherlines)

x = otherlines.split(cdelim)

for item in x:
    print(item)
    print("\n\nSWITCHING TO NEXT ONE\n\n")
