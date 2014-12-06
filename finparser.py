# -*- encoding: utf-8 -*-
# FIXME: make alternative form handling work even if 2 different postfixes matched
import itertools

known_verbs=['anna', 'poista', 'on']
known_nouns=['op', 'voice']

NULL=0
QUESTION=1
TO=2
FROM=4
ON=8

def matchpostfix(word, postfix):
	if len(postfix) >= len(word):
		return False
	if word[-len(postfix):] == postfix:
		return True
	return False

def combinations(iterable):
	result=[]
	for r in xrange(len(iterable)+1):
		[result.append(i) for i in itertools.combinations(iterable, r)]
	return result

def getroot(word, postfix):
	 return word[:-len(postfix)]
	
def degradate(origroot):
	gradate=[('kk', 'k'), ('pp', 'p'), ('tt', 't'), ('k', 'j'), ('k', 'v'), ('k', ''), ('p', 'v'), ('t', 'd'), ('t', '')]
	
	roots=set([origroot])
	for applygradate in combinations(gradate):
		root=origroot
		for original, gradated in applygradate:
			if gradated != '' and gradated in root: # doesn't handle gradate-to-null yet
				root=root.replace(gradated, original)
				roots.add(root)
	
	return roots

def deconjugate(word):
	postfixes=[('ko', QUESTION), ('kö', QUESTION),
	            ('lle', TO), ('ille', TO),
	            ('lta', FROM), ('ilta', FROM), ('ltä', FROM), ('iltä', FROM),
	            ('lla', ON), ('illa', ON), ('llä', ON), ('illä', ON)]
	
	results=set([(word, NULL)])
	for postfix, role in postfixes:
		if matchpostfix(word, postfix):
			root=getroot(word, postfix)
			results.add((root, role))
			for root, inflects in deconjugate(root):
				results.add((root, role | inflects))
	
	return results

def tokenize(text):
	verbs=[]
	nouns=[]
	unknowns=[]
	question=False
	for word in text.split():
		for root, inflects in deconjugate(word):
			case=(TO | FROM | ON) & inflects
			
			
			verbforms=[] # root
			nounforms=[] # root, case
			unknownforms=[] # root, case
			for root in degradate(root):
				if root in known_verbs and not case:
					verbforms.append(root)
				elif root in known_nouns:
					nounforms.append((root, case))
				else:
					unknownforms.append((root, case))
			
			if verbforms:
				verbs+=verbforms
			elif nounforms:
				nouns+=nounforms
			else:
				unknowns.append(unknownforms)
			if QUESTION & inflects:
				question=True
	return verbs, nouns, unknowns, question

def selectnick(alternatives):
	return '/'.join(alternatives)

def getmodes(nouns):
	return [root for root, inflects in filter((lambda (root, inflects): root in ['op', 'voice'] and not inflects), nouns)]

def getnicks(unknowns, nickcase):
	nicks=[]
	for word in unknowns:
		possible=[]
		for root, inflects in word:
			if nickcase & inflects:
				possible.append(root)
		if possible:
			nicks.append(selectnick(possible))
	return nicks

def nickmodecmd(cmdname, isquestion, nickcase, verbs, nouns, unknowns, question):
		if isquestion and not question:
			print "needs to be question"
			return None
		elif not isquestion and question:
			print "can't be question"
			return None
		
		modes=getmodes(nouns)
		if not modes:
			print "lacks mode"
			return None
		
		nicks=getnicks(unknowns, nickcase)
		if not nicks:
			print "lacks nick"
			return None
		
		return '%s:\n\tnicks: %s\n\tmodes: %s' % (cmdname, ', '.join(nicks), ', '.join(modes))

def parse(text):
	for i in [',','.',';',':','?','!']:
		text=text.replace(i, '')
	verbs, nouns, unknowns, question = tokenize(text)
	
	# There should be one verb
	if not verbs:
		print "No verb"
		return None
	if len(verbs) > 1:
		print "Too many verbs: %s" % ' '.join(verbs)
		return None
	verb=verbs[0]
	
	if verb=='on':
		return nickmodecmd('QUERY', True, ON, verbs, nouns, unknowns, question)
	elif verb=='anna':
		 return nickmodecmd('SET MODE', False, TO, verbs, nouns, unknowns, question)
	elif verb=='poista':
		return nickmodecmd('UNSET MODE', False, FROM, verbs, nouns, unknowns, question)
	return '?'

while True:
	line=raw_input('> ')
	if not line: break
	print parse(line)
