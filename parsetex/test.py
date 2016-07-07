import sys #handling arguments passed to function
import glob #file path handling
import os #checking files and writing to/from files
import re #regex matching
import numpy as np #for use in pyplot
import matplotlib.pyplot as pl #used to plot graphs
import multiprocessing as mp #drastic speedups when implemented on an i7-4700HQ
import heapq #to find n largest elements in makegraph

def strip (param):
    return param.strip()

class equation:
    def __init__(self,eqtext, desig = 'latex'):
        self.text = eqtext
        self.type = desig
        self.prevsent = ""
        self.nextsent = ""
        self.prevsenttoks = []
        self.nextsenttoks = []

f1 = open('1506/1506.07597.tex')

text = f1.read()

text = re.sub(r'(?m)^%+.*$','',text)
text = re.sub(r"(?m)([^\\])\%+.*?$",r'\1',text)
text = re.sub(r'\\begin\{comment\}.*?\\end\{comment\}','',text,re.DOTALL)
#series of regex expressions
a = re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}',text,re.DOTALL)
b = re.findall(r'\\begin\{multline\}(.*?)\\end\{multline\}',text,re.DOTALL)
c = re.findall(r'\\begin\{gather\}(.*?)\\end\{gather\}',text,re.DOTALL)
d = re.findall(r'\\begin\{align\}(.*?)\\end\{align\}',text,re.DOTALL)
e = re.findall(r'\\begin\{flalign\*\}(.*?)\\end\{flalign\*\}',text,re.DOTALL)
f = re.findall(r'\\begin\{math\}(.*?)\\end\{math\}',text,re.DOTALL)

g = re.findall(r'[^\\]\\\[(.*?)\\\]',text,re.DOTALL)
h = re.findall(r'\$\$([^\^].*?)\$\$',text,re.DOTALL)

l = re.findall(r'[^\\]\$(.*?)\$',text,re.DOTALL)
m = re.findall(r'\\\((.*?)\\\)',text,re.DOTALL)

net = [a,b,c,d,e,f,g,h,l,m]

for x in net:
    print(len(x))


total = a+b+c+d+e+f+g+h+m
total = map(strip,total)
print(len(total))
for x in total:
    print(type(x) is str)
cdelim = "CUSTOMDELIMITERHERE"

newtext = re.sub(r'[^\\]\$|\\\(|\\\)',cdelim,newtext)

a = newtext.split(cdelim)
a = map(strip,a)

print("HERE WE GO")

count = 0
for x in a:
    print("EVALUATING")
    print(x)
    if x in total:
        print("FOUND MATCH")
        print(x)
        count+=1
    if x in l:
        print("WTF")
print("Expected: {}\nActual: {}".format(len(total),count))
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
