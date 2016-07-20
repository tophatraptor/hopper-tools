#!/usr/bin/env python
#proctext.py - a less naive, class-based version of parsetex.py
#Jay Dhanoa
#before running this script, run getarxivdatav2.py for the corresponding folder
import sys #handling arguments passed to function
import glob #file path handling
import os #checking files and writing to/from files
import re #regex matching
import numpy as np #for use in pyplot
import matplotlib.pyplot as pl #used to plot graphs
import multiprocessing as mp #drastic speedups when implemented on an i7-4710HQ
import heapq #to find n largest elements in makegraph
import pickle #serializing to/from disk
from nltk.tokenize import word_tokenize, sent_tokenize
import gc

#CLASSES

#equation class - for now, it's only going to hold the tokens
class equation:
    def __init__(self,eqtext, desig = 'latex'):
        self.text = eqtext
        self.type = desig
        self.prevsent = ""
        self.nextsent = ""
        self.prevsenttoks = []
        self.nextsenttoks = []
        #pst & nst generated with nltk

    def gentokens():
        self.prevsenttoks = word_tokenize(self.prevsent)
        self.nextsenttoks = word_tokenize(self.nextsent)

class document:
    def __init__(self, fname,textarray):
        self.name = fname
        self.array = textarray

    def get_equations(self):
        ret = []
        for item in self.array:
            if type(item) is equation:
                ret.append(item)
        return(ret)


class archive:
    def __init__(self,directory_name,dictionary):
        self.dir = directory_name
        self.docdict = dictionary
    def save(self):
        print(self.dir)
        outfilepath = self.dir + ".pkl"
        if os.path.isfile(outfilepath):
            outfile = open(outfilepath)
        else:
            outfile = open(outfilepath,'w+')
        pickle.dump(self,outfile)
        outfile.close()


def strip (param):
    return param.strip()

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
    procname = re.findall(r'\/([0-9.]*.tex)',filename)[0]
    f1 = open('example.txt','rt')
    text = f1.read()
    #remove comments
    text = re.sub(r'(?m)^%+.*$','',text) #remove all comments at beginning of lines
    text = re.sub(r"(?m)([^\\])\%+.*?$",r'\1',text) #remove all remaining comments
    text = re.sub(r'\\begin\{comment\}.*?\\end\{comment\}','',text,re.DOTALL)
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
    h = re.findall(r'\$\$([^\^].*?)\$\$',text,re.DOTALL)

    #tabular regex matching
    #i = re.findall(r'\\begin\{table\*\}(.*?)\\end\{table\*\}', text, re.DOTALL)
    #j = re.findall(r'\\begin\{table\}(.*?)\\end\{table\}', text, re.DOTALL)
    #k = re.findall(r'\\begin\{tablular\}(.*?)\\end\{tabular\}', text, re.DOTALL)
    l = re.findall(r'[^\\]\$(.*?)\$',text,re.DOTALL)
    m = re.findall(r'\\\((.*?)\\\)',text,re.DOTALL)

    #finds is a list of lists of found expressions
    #currently does not include the tabular regex
    finds = [a,b,c,d,e,f,g,h]
    countdict = {}

    #every re.findall command generates a list of tokens that match the expression
    #iterate over all of those, and then find everything matching the '\token' format
    for x in finds:
        for item in x:
            #match regex for mathematical token
            found = re.findall(r'\\\w+|d[a-z]|[^\\A-Za-z](d[\^]?[0-9]?[[:space:]]?[a-z])|[a-zA-z]\([a-zA-z]\)',item)
            map(strip,found)
            count(found,countdict)

    total = a+b+c+d+e+f+g+h
    total = map(strip,total)
    cdelim = " CUSTOMDELIMITERHERE "
    newtext = text
    newtext = re.sub(r'(?s)\\begin\{equation\}(.*?)\\end\{equation\}',cdelim + r'\1' + cdelim,newtext)
    newtext = re.sub(r'(?s)\\begin\{multline\}(.*?)\\end\{multline\}',cdelim + r'\1' + cdelim,newtext)
    newtext = re.sub(r'(?s)\\begin\{gather\}(.*?)\\end\{gather\}',cdelim + r'\1' + cdelim,newtext)
    newtext = re.sub(r'(?s)\\begin\{align\}(.*?)\\end\{align\}',cdelim + r'\1' + cdelim,newtext)
    newtext = re.sub(r'(?s)\\begin\{flalign\*\}(.*?)\\end\{flalign\*\}',cdelim + r'\1' + cdelim,newtext)
    newtext = re.sub(r'(?s)\\begin\{math\}(.*?)\\end\{math\}',cdelim + r'\1' + cdelim,newtext)
    newtext = re.sub(r'(?s)[^\\]\\\[(.*?)\\\]',cdelim + r'\1' + cdelim,newtext)
    newtext = re.sub(r'(?s)\$\$([^\^].*?)\$\$',cdelim + r'\1' + cdelim,newtext)
    # dispeqs = re.findall(r'(?s) CUSTOMDELIMITERHERE (.*?) CUSTOMDELIMITERHERE',newtext,re.DOTALL)
    dispeqs = re.findall(r'(?s)' + cdelim + r'(.*?)' + cdelim,newtext)
    map(strip,dispeqs)
    textlist = newtext.split(cdelim)
    textlist = map(strip,textlist)
    for i in range(len(textlist)):
        if textlist[i] in dispeqs:
            textlist[i] = equation(textlist[i])
    newdoc = document(procname,textlist)
    print(newdoc)
    exit()
    return (countdict,newdoc)

    #Use Matplotlib to plot results
    #takes one argument (necessary for pool.map)
    #tuple of arguments lets us pass multiple arguments

    #Use Matplotlib to plot results
    #takes one argument (necessary for pool.map)
    #tuple of arguments lets us pass multiple arguments

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
    print("Initialized {} threads".format(mp.cpu_count()))
    #error handling for missing metadata file
    if not os.path.isfile(metadata):
        print("Error: file not found. Make sure you've entered the correct directory AND have run getarxivdatav2.py for said directory.")
        sys.exit()
    #load in the list of files and their categories
    filecats = open(metadata,'r')
    lines = filecats.readlines()
    print("Read in file metadata.")
    #each line of the form 'filename.tex' 'category'
    #this changes it to just 'filename' and 'category'
    lines = map(proc,lines)
    #dictionary of categories
    #keys are category names
    #values are count dictionaries of tokens in papers of the category
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
    if len(lines)!=len(filelist):
        print("Warning: possible mismatch - the number of .tex files has changed since metadata was last generated. Rerun getarxivdatav2.py to update metadata")
    print("Getting token counts of files...")
    #filedictlist is the result of makedict mapped over each filename
    #filelist[0] corresponds to filedictlist[0]
    mergedlist = map(makedict,filelist)
    filedictlist, doclist = zip(*mergedlist)
    dirarchive = archive(path[:-1],{f.name:f for f in doclist})
    #iterate over filelist & filedictlist
    #generate count dictionary for that file
    #merge with count dictionary for the file's category
    #overall count dictionary
    totdict = {}
    #iterate over files, merge counts with their respective categories
    #non-thread safe, so iteration is serial
    for index, item in enumerate(filelist):
        cat = fnamedict[os.path.basename(filelist[index])]
        merge(filedictlist[index],categories[cat])
        #merge category counts with overall count dictionary
        merge(filedictlist[index],totdict)
    #add the total dictionary to categories for graph generation
    categories['overall'] = totdict
    print("Categorical token counting complete.")
    #handles closing of multiple processes
    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
