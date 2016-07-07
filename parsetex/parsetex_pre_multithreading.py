#!/usr/bin/env python

#parsetex.py
#Jay Dhanoa
#before running this script, run getarxivdatav2.py
#if arxivdata.txt isn't already present)
import sys
import glob
import os
import re
import numpy as np
import matplotlib.pyplot as pl
import urllib
import multiprocessing as mp
from operator import itemgetter

#path to directory with text files
path = '1506/'

#iterates over a list of found tokens, and increments
#dictionary token count, or initializes it to zero
def count(found,countdict):
    for item in found:
        if item in countdict:
            countdict[item] +=1
        else:
            countdict[item] = 1

#merge two counting dictionaries
#takes cdic(child) and pdic(parent)
def merge(cdic,pdic):
    for key in cdic:
        if key in pdic:
            pdic[key] += cdic[key]
        else:
            pdic[key] = cdic[key]

#print sorted dictionary
def psd(dic):
    for key, value in sorted(dic.items(), key=lambda x: (-x[1], x[0])):
        print(key,value)

#split method on period for multithreaded mapping
def proc(instr):
    val = instr.split()
    val[1] = (val[1].split('.'))[0]
    return val

#makes a dictionary of counted values
def makedict(filename):
    f1 = open(filename,'rt')
    text = f1.read()
    #series of regex expressions
    a = re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}',text,re.DOTALL)
    b = re.findall(r'\\begin\{multline\}(.*?)\\end\{multline\}',text,re.DOTALL)
    c = re.findall(r'\\begin\{gather\}(.*?)\\end\{gather\}',text,re.DOTALL)
    d = re.findall(r'\\begin\{align\}(.*?)\\end\{align\}',text,re.DOTALL)
    e = re.findall(r'\\begin\{flalign\*\}(.*?)\\end\{flalign\*\}',text,re.DOTALL)
    f = re.findall(r'\\begin\{math\}(.*?)\\end\{math\}',text,re.DOTALL)
    #display mode equation for '\[...\]'
    #specifies that it should be preceded by a non-backslash character
    #won't count instances where display mode is the very first character the file
    #that should never be the case
    g = re.findall(r'[^\\]\\\[(.*?)\\\]',text,re.DOTALL)
    #finds is a list of lists of found expressions
    finds = [a,b,c,d,e,f,g]
    countdict = {}
    #every re.findall command generates a list of tokens that match the expression
    #iterate over all of those, and then find everything matching the '\token' format
    for x in finds:
        for item in x:
            found = re.findall(r'\\\w+',item)
            count(found,countdict)
    return countdict

#Use Matplotlib to plot results
def makegraph(indict,fname):
    countdict = {}
    #plotting all values takes a very long time
    #optimal for readability/speed to only plot values larger
    #than 1/10th the highest value
    limit = max(list(indict.values()))/10
    for x in indict:
        if(indict[x]>limit):
            countdict[x] = indict[x]
    outdir = 'graphs/' + fname + '.png'
    #image dimensions
    pl.figure(figsize=(16,8),dpi=100)
    pl.axis('tight')
    X = np.arange(len(countdict))
    #turn the new dictionary into a list of tuples, sorted by count value
    items = sorted(countdict.items(), key=lambda x:x[1], reverse=True)
    xvals, yvals = zip(*items)
    pl.bar(X, yvals, align='center', width=0.5)
    pl.xticks(X, xvals, rotation='vertical')
    ymax = max(countdict.values()) + 1
    pl.ylim(0, ymax)
    #saves the image to preexisting directory outdir
    #file name has the format 'categoryname.png'
    pl.savefig(outdir)


def main():
    #read in data
    #remove general subcategories
    pool = mp.Pool(processes=mp.cpu_count())
    filecats = open('arxivdata.txt','r')
    lines = filecats.readlines()
    print("Read in file metadata.")
    lines = pool.map(proc,lines)
    #dictionary of categories - will store values of
    categories = {}
    #dictionary of filenames and their associated categories
    fnamedict = {}

    #populate the respective dictionaries
    for x in lines:
        if x[1] not in categories:
            categories[x[1]] = {}
        fnamedict[x[0]] = x[1]
    print("Populated dictionaries.")
    #list of tex files in the directory specified by path
    filelist= glob.glob(os.path.join(path,'*.tex'))
    print("Getting token counts of files...")
    #iterate over file
    #generate count dictionary for that file
    #merge with count dictionary for the file's category
    for infile in filelist:
        cat = fnamedict[os.path.basename(infile)]
        filedict = makedict(infile)
        merge(filedict,categories[cat])
    print("Categorical token counting complete.")
    #produce graphs
    print("Generating graphs...")
    i=1
    tot = len(categories.keys())
    for cat in categories:
        print("Processing {} ({}/{})".format(cat,i,tot))
        makegraph(categories[cat],cat)
        i+=1

if __name__ == '__main__':
    main()
