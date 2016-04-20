# decompose LaTeX file into equations and text
# (assumes file has been demacro'd)

import re, argparse
import ntpath, os.path
import glob
import multiprocessing
from itertools import repeat

def match_start(start):
    if re.search(r'begin', start):
        return re.sub(r'begin', 'end', start)
    elif start == '\\[':
        return '\\]'
    elif start == r'\$\$':
        return r'\$\$'
    else:
        return ''

def delabel(term):
    if term.find("*")<0:
        term = term.replace("equation","equation*")
        term = term.replace("align","align*")
        term = term.replace("eqnarray","eqnarray*")
        term = term.replace("multline","multline*")
    return term

def decomment(line):
    match    = re.search(r"([^\n%]*)(.*)", line)
    newline  = match.group(1)
    line     = match.group(2)
    while re.search(r"\\$", newline):
        if len(line)==0:
            break
        match    = re.search(r"([^\n%]*)(.*)", line[1:])
        newline += '%'+ match.group(1)
        line     = match.group(2)
    return newline+'\n'

def decomposeTeX(inputDoc):

	# each element is separate line from inputDoc
	unread   = open(inputDoc, 'r').readlines()

	formulaPat = re.compile(r"(\\begin{equation}|\\begin{equation\*}|\\begin{align}|\\begin{multline\*}|\\begin{align\*}|\\begin{eqnarray}|\\begin{eqnarray\*}|\\\[|\$\$)(.*)")

	idx            = 0
	eqn_idx        = []
	text_idx       = []
	decomposed_doc = []

	while len(unread)>0:
	    current      = unread[0]
	    unread       = unread[1:]
	    matchFormula = formulaPat.search(current)
	    if matchFormula:
	        start = matchFormula.group(1)
	        if len(start) == 0:
	          continue
	        if (start == '\\[') & (current.find('\\[')>0) & (current[current.find('\\[')-1]=='\\'):
	            continue
	        end          = match_start(start)
	        formula_temp = []
	        formula_temp.append(delabel(start)+'\n')
	        if re.search(r'\S',matchFormula.group(2)):
	            current = matchFormula.group(2)+'\n'
	        else:
	        	if len(unread) == 0:
	        		break
				current = unread[0]
				unread = unread[1:]
	        while current.find(end)<0:
	            if re.search(r'\S', current):
	                formula_temp.append(current)
	                if re.search(r"\\label", current):
	                    labelFlag = True
	            if len(unread)==0:
	                break
	            current = unread[0]
	            unread = unread[1:]
	        ind = current.find(end)
	        #formula_temp.append(current[0:ind]+'\n')
	        formula_temp.append(current[0:ind]+delabel(end)+'\n')
	        if len(current)>ind+len(end)+1:
	            unread = [ current[ind+len(end)] ] + unread
	        decomposed_doc.append(' '.join(formula_temp).strip())
	        eqn_idx.append(idx)
	        idx += 1
	    else:
	        if idx == 0:
	            decomposed_doc.append(decomment(current.strip()))
	            text_idx.append(idx)
	            idx += 1
	        elif len(eqn_idx) > 0 and eqn_idx[-1] == (idx-1):
	            decomposed_doc.append(decomment(current.strip()))
	            text_idx.append(idx)
	            idx += 1
	        else:
	            decomposed_doc[-1] = decomposed_doc[-1] + decomment(current.strip())
	return decomposed_doc, eqn_idx, text_idx

def construct_p2v_data((inputDoc, p2vDir, p2v_metaDir)):
	
	# decompose LaTeX document
	try:
		decomposed_doc, eqn_idx, text_idx = decomposeTeX(inputDoc)
	except:
		print "Error in {}".format(inputDoc)
	
	#decomposed_doc, eqn_idx, text_idx = decomposeTeX(inputDoc)

	p2vDoc      = os.path.join(p2vDir, ntpath.basename(inputDoc).replace('.tex', '') + ".p2v")
	p2v_metaDoc = os.path.join(p2v_metaDir, ntpath.basename(inputDoc).replace('.tex', '') + ".meta")
	p2v_doc     = open(p2vDoc, 'w')
	p2v_meta    = open(p2v_metaDoc, 'w')

	WINDOW_SIZE = 200
	eqn_number  = 1
	for eidx in eqn_idx:
		if eidx == 0:
			text_above = ['']
		else:

			text_above = ' '.join(decomposed_doc[eidx-1].strip().split())
			text_above = text_above.lower() # lower case
			text_above = re.sub('\$.*?\$', '', text_above) # remove inline math
			text_above =	re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', '', text_above) # remove other sections
			text_above =	re.sub(r'.*?\\end\{.*?\}', '', text_above) # possible that \begin is missing
			text_above =	re.sub(r'\\begin\{.*?\}.*?', '', text_above) # possible that \end is missing
			text_above =	re.sub(r'\\[sub]*section\{.*?\}', '', text_above) # remove other sections

			text_above = text_above.split()[-WINDOW_SIZE:] 

		if eidx == (len(decomposed_doc)-1):
			text_below = ['']
		else:
			text_below = ' '.join(decomposed_doc[eidx+1].strip().split())
			text_below = text_below.lower() # lower case
			text_below = re.sub('\$.*?\$', '', text_below) # remove inline math
			text_below =	re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', '', text_below) # remove other sections
			text_below =	re.sub(r'.*?\\end\{.*?\}', '', text_below) # possible that \begin is missing
			text_below =	re.sub(r'\\begin\{.*?\}.*?', '', text_below) # possible that \end is missing
			text_below =	re.sub(r'\\[sub]*section\{.*?\}', '', text_below) # remove other sections

			text_below = text_below.split()[:WINDOW_SIZE]


		paragraph = ' '.join(text_above + text_below)
		#print len(paragraph.split())
		# paragraph = paragraph.lower() # lower case
		# paragraph = re.sub('\$.*?\$', '', paragraph) # remove inline math
		# paragraph =	re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', '', paragraph) # remove other sections
		# paragraph =	re.sub(r'.*?\\end\{.*?\}', '', paragraph) # possible that \begin is missing
		# paragraph =	re.sub(r'\\begin\{.*?\}.*?', '', paragraph) # possible that \end is missing
		# paragraph =	re.sub(r'\\[sub]*section\{.*?\}', '', paragraph) # remove other sections
		#paragraph = re.sub(r"\\[a-b]*{*.*?}", '', paragraph) # remove things like \\cite{blah} [needs work]

		if len(paragraph.split()) < 200:
			continue
		paragraph = paragraph.replace('.', ' . ')
		paragraph = paragraph.replace('"', ' " ')
		paragraph = paragraph.replace(',', ' , ')
		paragraph = paragraph.replace('(', ' ( ')
		paragraph = paragraph.replace(')', ' ) ')
		paragraph = paragraph.replace('!', ' ! ')
		paragraph = paragraph.replace('?', ' ? ')
		paragraph = paragraph.replace(';', ' ; ')
		paragraph = paragraph.replace(':', ' : ')

		paragraph_id   = inputDoc + '_' + str(eqn_number)
		line           = paragraph_id + ' ' + paragraph
		p2v_doc.write(line + '\n')

		meta_data      = paragraph_id + '\t' + decomposed_doc[eidx].replace('\n', '')
		p2v_meta.write(meta_data + '\n')
		eqn_number += 1


def main():
	# parse command-line argument
	parser = argparse.ArgumentParser(description = 'extract and convert equations from tex to png')

	parser.add_argument('inputDoc', help = 'input directory')
	parser.add_argument('p2vDir', help = 'output directory')
	parser.add_argument('p2v_metaDir', help = 'output directory')
	parser.add_argument('-d', '--directory', action='store_true', help='indicates that inputFile is a directory tex files and outputFile is a directory')

	args = parser.parse_args()

	if args.directory:
		doc_list = glob.glob(args.inputDoc + '/*.tex')
		pool     = multiprocessing.Pool(processes=24)
		pool.map(construct_p2v_data, zip(doc_list, repeat(args.p2vDir), repeat(args.p2v_metaDir)))
	else:
		construct_p2v_data((args.inputDoc, args.p2vDir, args.p2v_metaDir))

	return


if __name__ == "__main__":
    main()
