import os, codecs, pickle, time
import resource

import nltk
from nltk.tokenize import RegexpTokenizer
tokenizer = RegexpTokenizer(r'\w+')
bigram_measures  = nltk.collocations.BigramAssocMeasures()
from nltk.collocations import *

import ahocorasick
from collections import defaultdict
import pandas as pd
import numpy as np
import argparse

def limit_memory(maxsize):
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (maxsize, hard))

def main():

        limit_memory(25000000000)
	parser = argparse.ArgumentParser(description = 'extract and convert equations from tex to png')

	parser.add_argument('corpus_dir', help = 'input directory')
	parser.add_argument('cache_file_corpus', help = 'output directory')
	parser.add_argument('cache_file_byDoc', help = 'output directory')
	parser.add_argument('pmi_output_file', help = 'output directory')
	parser.add_argument('coccur_file', help = 'output directory')
	args = parser.parse_args()

        full_corpus, byDoc = corpus_dir_to_str( corpus_dir = args.corpus_dir, 
                                                cache_file_corpus = args.cache_file_corpus,
                                                cache_file_byDoc  = args.cache_file_byDoc)


        print "tokenizing"
        full_tokens          = tokenizer.tokenize(full_corpus)
        del full_corpus
        uni_fd               = nltk.FreqDist(full_tokens)
        bi_fd                = nltk.FreqDist(nltk.bigrams(full_tokens))
        
        bi_pmi               = BigramCollocationFinder(uni_fd, bi_fd)
        bi_pmi.apply_freq_filter(20)
        
        #valid_unigrams = [' '+w+' ' for w in uni_fd.keys() if uni_fd[w] > 50 and len(w) >= 3]
        valid_unigrams = [' '+w+' ' for w in uni_fd.keys() if uni_fd[w] > 100 and len(w) >= 3]
        valid_bigrams  = [' '+w1+' '+w2+' ' for w1,w2 in bi_pmi.nbest(bigram_measures.pmi, 15000) if len(w1) >= 3 and len(w2) >= 3]
        vocab = valid_unigrams + valid_bigrams
    
        print "vocab size = {} tokens".format(len(vocab))


        A = ahocorasick.Automaton()
        for index, word in enumerate(vocab):
            A.add_word(str(word), (str(word), len(word)))
        A.make_automaton()

        INCLUSION_WINDOW    = 50
        EXCLUSION_WINDOW    = 5
        remove_bi = [w for w,n in uni_fd.most_common(20)]


        if os.path.isfile(args.coccur_file):
            print "Loading Co-occurence Counts"
            counts = pickle.load(open(args.coccur_file, 'r'))
        else:
            print "Computing Co-occurence Counts"
            counts = {}
            num_docs = 0
            global_start = time.time()
            start        = time.time()

            for doc in byDoc.keys():
                doc_grep = []
                for item in A.iter(byDoc[doc].encode('utf8', 'ignore')):
                    doc_grep.append(item)
                num_docs += 1
                if num_docs % 1000 == 0:
                    docs_per_sec = num_docs / float(time.time()-global_start)
                    time_left_min    = ((len(byDoc.keys())-num_docs)/docs_per_sec)/60.0
                    print "({}, {}) Estimated Time Left: {} mins".format(num_docs, time.time()-start, time_left_min)
                    start = time.time()
                for index, elt in enumerate(doc_grep):
                    
                    (loc, (head_word, head_len)) = elt
                    if ' ' not in head_word.lstrip(' ').rstrip(' '):
                        continue
                    if len(set(head_word.split()).intersection(set(remove_bi))) != 0:
                        continue
                    
                    left_idx_set  = range(max(0, index-INCLUSION_WINDOW), max(0, index-EXCLUSION_WINDOW))
                    if len(left_idx_set) > 0:
                        if head_word not in counts:
                            counts[head_word] = defaultdict(int)
                        for l_idx in left_idx_set:
                            counts[head_word][doc_grep[l_idx][1][0]] += 1
                            
                    right_idx_set = range(min(len(doc_grep)-1, index + EXCLUSION_WINDOW), min(len(doc_grep)-1, index + INCLUSION_WINDOW))
                    if len(right_idx_set) > 0:
                        if head_word not in counts:
                            counts[head_word] = defaultdict(int)
                        for r_idx in right_idx_set:
                            counts[head_word][doc_grep[r_idx][1][0]] += 1  
            
            print "Total Time = {}".format((time.time()-global_start)/60.0)
            pickle.dump(counts, open(args.coccur_file, 'w'))
            del doc_grep

        print "compute valid_pair"
        remove_bi = [w for w,n in uni_fd.most_common(20)]
        count_df = pd.DataFrame(data = 0, index = counts.keys(), columns = vocab)
        valid_pairs = []
        test = {}
        idx = 1
        tmp = 0
        for k1 in counts.keys():
            if len(set(k1.split()).intersection(set(remove_bi))) != 0: # dont need anymore?
                continue
            if idx % 1000 == 0:
                print idx
            for k2 in counts[k1].keys():
                if len(set(k2.split()).intersection(set(remove_bi))) != 0: # dont need anymore?
                    continue
                if ' ' in k1.lstrip(' ').rstrip(' ') and counts[k1][k2] > 10 and commonOverlapKmp(k1.lstrip(' ').rstrip(' '), k2.lstrip(' ').rstrip(' ')) == 0 and commonOverlapKmp(k2.lstrip(' ').rstrip(' '), k1.lstrip(' ').rstrip(' ')) == 0:
                    count_df.at[k1, k2] += counts[k1][k2]
                    if (k2,k1) not in test:
                        test[(k1,k2)] = 1
                        valid_pairs.append((k1,k2))
            idx += 1
        print "number of valid pairs = {}".format(len(valid_pairs))

        print "Compute PMI"
        pmi_df_rows = []
        feat_counts  = count_df.sum(axis=0)
        total_uni_bi = sum(uni_fd.values()) + sum(bi_fd.values())
        total_bi = sum(bi_fd.values())
        total_uni = sum(uni_fd.values())
        print "total = {}".format(len(valid_pairs))
        idx = 0
        s1 = time.time()
        for w1, w2 in valid_pairs:
            if idx % 100000 == 0:
                print "{}, {}".format(idx, time.time()-s1)
                
            f   = count_df.at[w1,w2]
            num =  f / float(feat_counts[w2])
            
            w1_f = w1.lstrip(' ')
            w1_f = w1_f.rstrip(' ')
            if ' ' in w1_f:     
                bi_w1, bi_w2 = w1_f.split()
                #denom = bi_fd[(bi_w1, bi_w2)] / float(total_uni_bi)
                denom = bi_fd[(bi_w1, bi_w2)] / float(total_bi)
                denom_freq = bi_fd[(bi_w1, bi_w2)]
            else:
                #denom = uni_fd[w1_f] / float(total_uni_bi)
                denom = uni_fd[w1_f] / float(total_uni)
                denom_freq = uni_fd[w1_f]
            pmi_df_rows.append([w1.lstrip(' ').rstrip(' '), w2.lstrip(' ').rstrip(' '), np.log(num/denom), f, denom_freq])
            idx += 1
            
        pmi_df = pd.DataFrame(pmi_df_rows, columns=['w1', 'w2', 'pmi', 'freq', 'denom.freq'])

        pmi_df = pmi_df.sort_values('pmi', ascending=False)
        pmi_df.to_csv(args.pmi_output_file, encoding='utf-8')

	return

def corpus_dir_to_str(corpus_dir, cache_file_corpus=None, cache_file_byDoc=None, force=False):
    if (cache_file_corpus is not None and cache_file_byDoc is None) or (cache_file_corpus is  None and cache_file_byDoc is not None):
        print "must set both cache_file"
        return(("", ""))
    if (cache_file_corpus is not None and os.path.isfile(cache_file_corpus)) and not force:
        full_corpus = pickle.load(open(cache_file_corpus, 'r'))
        by_doc       = pickle.load(open(cache_file_byDoc, 'r'))
    else:
        corpus_filenames = [os.path.join(corpus_dir, f) for f in os.listdir(corpus_dir)]
        print "{} files".format(len(corpus_filenames))
        by_doc           = {}
        start = time.time()
        for filename in corpus_filenames:
            doc              = codecs.open(filename, 'r', 'utf8', 'ignore').read().lower()
            by_doc[filename] = doc
        full_corpus = ' '.join([d for d in by_doc.values()]) 
        print "{} seconds to read entire corpus".format(time.time()-start)
        if cache_file_corpus is not None:
            pickle.dump(full_corpus, open(cache_file_corpus, 'w'))
            pickle.dump(by_doc, open(cache_file_byDoc, 'w'))
    return((full_corpus, by_doc))

def commonOverlapKmp(text1, text2):  
    # Cache the text lengths to prevent multiple calls.  
    text1_length = len(text1)  
    text2_length = len(text2)  
    # Eliminate the null case.  
    if text1_length == 0 or text2_length == 0:  
        return 0  
    # Truncate the longer string.  
    if text1_length > text2_length:  
        text1 = text1[-text2_length:]  
    elif text1_length < text2_length:  
        text2 = text2[:text1_length]  
    text_length = min(text1_length, text2_length)  
    # Quick check for the worst case.  
    if text1 == text2:  
        return text_length  

    # Build partial match table from text2.  
    table = [0] * text_length  
    table[0] = -1  
    #table[1] = 0  
    pos = 2  
    cnd = 0  
    while pos < text_length:  
        if text2[pos - 1] == text2[cnd]:  
            cnd += 1  
            table[pos] = cnd  
            pos += 1  
        elif cnd > 0:  
            cnd = table[cnd]  
        else:  
            table[pos] = 0  
            pos += 1  

    # Search text1.  
    m = 0  
    i = 0  
    while m + i < text_length:  
        if text2[i] == text1[m + i]:  
            i += 1  
            if m + i == text_length:  
                return i  
        else:  
            m += i - table[i]  
            if table[i] > -1:  
                i = table[i]  
            else:  
                i = 0  
    return 0  

if __name__ == "__main__":
    main()
