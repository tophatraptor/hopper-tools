#!/usr/bin/env python
#parsetex.py
#Jay Dhanoa
#before running this script, run getarxivdatav2.py for the corresponding folder
import sys #handling arguments passed to function
import glob #file path handling
import os #checking files and writing to/from files
import re #regex matching
import numpy as np #for use in pyplot
import matplotlib.pyplot as pl #used to plot graphs
import multiprocessing as mp #drastic speedups when implemented on an i7-4700HQ
import heapq #to find n largest elements in makegraph

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

#split on period function for multithreaded mapping
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
    #g matches '\[...\]'
    #specifies that it should be preceded by a non-backslash character
    #won't count instances where this is the very first instance in the file
    #that should never be the case
    g = re.findall(r'[^\\]\\\[(.*?)\\\]',text,re.DOTALL)
    h = re.findall(r'\$\$[^\^\_](.*?)\$\$',text,re.DOTALL)
    #tabular regex matching
    #i = re.findall(r'\\begin\{table\*\}(.*?)\\end\{table\*\}', text, re.DOTALL)
    #j = re.findall(r'\\begin\{table\}(.*?)\\end\{table\}', text, re.DOTALL)
    #k = re.findall(r'\\begin\{tablular\}(.*?)\\end\{tabular\}', text, re.DOTALL)

    #finds is a list of lists of found expressions
    #currently does not include the tabular regex
    finds = [a,b,c,d,e,f,g,h]
    countdict = {}
    #every re.findall command generates a list of tokens that match the expression
    #iterate over all of those, and then find everything matching the '\token' format
    for x in finds:
        for item in x:
            #match regex for mathematical token
            found = re.findall(r'\\\w+',item)
            count(found,countdict)
    return countdict

#Use Matplotlib to plot results
def makegraph(indict,fname, outdir):
    countdict = {}
    #graphs will display the first disptoks most common tokens
    disptoks = 20
    #plotting all values takes a relatively long time
    #instead, will plot the 20 most frequently occurring tokens
    #sorted in descending order by frequency
    #returns the 20th largest value, and sets that as the cutoff
    limit = min(heapq.nlargest(disptoks,indict.values()))
    #assemble a dictionary of only tokens with frequencies higher than the cutoff
    for x in indict:
        if(indict[x]>limit):
            countdict[x] = indict[x]
            #specify outfile
    outfile = outdir + fname + '.png'
    #generate a 1600x800 image for each graph
    pl.figure(figsize=(16,8),dpi=100)
    pl.axis('tight')
    X = np.arange(len(countdict))
    #turn the new dictionary into a list of tuples, sorted by count value
    items = sorted(countdict.items(), key=lambda x:x[1], reverse=True)
    xvals, yvals = zip(*items)
    pl.bar(X, yvals, align='center', width=0.5)
    pl.xticks(X, xvals, rotation='vertical')
    #Setting title of the generated graph
    pl.title(str(disptoks) + " most common tokens in: " + fname)
    ymax = max(countdict.values()) + 1
    pl.ylim(0, ymax)
    #saves the image to outfile
    #file name has the format 'categoryname.png'
    pl.savefig(outfile)


def main():
    #default path to directory with tex files
    path = '1506/'
    #The program accepts a directory to be analyzed
    #The directory should have the LaTeX files (entered without the '/')
    if(len(sys.argv)>2):
        path = str(sys.argv[1]+'/')
        if not os.path.isdir(path):
            print("Error: passed parameter is not a directory")
            sys.exit()
    #per getarxivdatav2, the metadata for tex files in a folder
    #should be in a .txt file of the same name
    metadata = path[:-1] + '.txt'
    #read in data
    #remove general subcategories
    #initialize number of threads to the number of cpu cores
    pool = mp.Pool(processes=mp.cpu_count())
    #load in the list of files and their categories
    filecats = open(metadata,'r')
    lines = filecats.readlines()
    print("Read in file metadata.")
    #each line of the form 'filename.tex' 'category'
    #this changes it to just 'filename' and 'category'
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
    #filedictlist is the result of makedict mapped over each filename
    #filelist[0] corresponds to filedictlist[0]
    filedictlist = pool.map(makedict,filelist)
    #iterate over filelist & filedictlist
    #generate count dictionary for that file
    #merge with count dictionary for the file's category
    #overall countdict
    totdict = {}
    #iterate over files, merge counts with their respective categories
    for index, item in enumerate(filelist):
        cat = fnamedict[os.path.basename(filelist[index])]
        merge(filedictlist[index],categories[cat])
        #merge counts with overall count dictionary
        merge(filedictlist[index],totdict)
    #add the total dictionary to categories for graph generation
    categories['overall'] = totdict
    print("Categorical token counting complete.")
    #produce graphs
    print("Generating graphs...")
    #helper variable to avoid recalculation & display progress
    tot = len(categories.keys())
    graphpath = path[:-1]+'_graphs/'
    #if the directory doesn't already exist, generate it
    if not os.path.exists(graphpath):
        os.makedirs(graphpath)
    #generate graphs and display progress
    for index, cat in enumerate(categories):
        print("Processing {} ({}/{})".format(cat,index+1,tot))
        makegraph(categories[cat],cat, graphpath)
    #handles closing of multiple processes
    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
