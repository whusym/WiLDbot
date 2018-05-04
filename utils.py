import spacy
import wptools
import re
import wikipediaapi

print ('loading preambles..')
NLP_CORE = spacy.load('en_core_web_lg')
FIND_WIKI = wikipediaapi.Wikipedia('en')
ENTS_TYPE = ['PERSON', 'FACILITY', 'ORG', 'GPE', 'LOC', 'WORK_OF_ART', 'RETRIEVED_ENTRY']
NLP_VEC = spacy.load('en_core_web_lg')
print ('loading finished..')


def pre_process(query_str):
    '''
    pre-process the string and return a more cleaned-up string.
    '''
    # first, recursively remove the punctuations at the end of the query
    while not query_str[-1].isalnum():
        query_str = query_str[:-1]
    
    # substitute some special nouns
    sub_dict = {'(?i)wife': 'spouse', '(?i)husband': 'spouse'}  # ignore upper and lower case; we can add more 

    for i in sub_dict:
        query_str = re.sub(i, sub_dict[i], query_str)
    
    return query_str

def process_sen(sen, ent_match=True, model=NLP_CORE):
    '''
    Process the query sentence string into entity chunks
    
    sen: query string after pre_process
    
    ent_match (Default True): 
    boolean value to determine whether to search a matched entity pattern that Spacy may not recognize
    e.g. French Fifth Republic, French Polynesia.
    NB -- but in this query "How much did Pulp Fiction cost", it's hard to check "Pulp Fiction" if it's 
    detected by Spacy?
    
    model (Default NLP_CORE):
    the model used in processing. default value is the core large spacy english model.
    '''

    nlp = NLP_CORE
    sen = nlp(sen)
    sen_chunk = [chunk for chunk in sen.noun_chunks]
    
    # we use 'this_chunk' to store the chunk content and its metadata and use for return
    this_chunk = [] 
    sen_chunk_str = [chunk.text for chunk in sen.noun_chunks]
    
    # process each item in sen_chunk
    for j in sen_chunk_str:
        # remove the definite article
        if j.split()[0] == 'the':            
            j = ' '.join(j.split()[1:])   
        if j[-2:] == "'s":
            print (j)
            j = j[:-2]
        page_py = FIND_WIKI.page(j)
        if nlp(j).ents:
            page_py = FIND_WIKI.page(nlp(j).ents[0].text)
            if page_py.exists():
                this_chunk.append((nlp(j).ents[0].text, nlp(j).ents[0].label_, page_py.exists()))
            else:
                this_chunk.append((nlp(j).ents[0].text, nlp(j).ents[0].label_, None))
        elif page_py.exists():
            this_chunk.append((j, 'NONE', page_py.exists()))
        else:
            this_chunk.append((j, 'NO_ENTRY', False))
            
    # add additional chunk; hard code some common prompts
    if sen.text.split()[0].lower() == 'when':
        this_chunk.append(('time', 'NO_ENTRY', False))
        this_chunk.append(('date', 'NO_ENTRY', False))
        
    if sen.text.split()[0].lower() == 'where' or (sen.text.split()[0].lower() == 'in' and sen.text.split()[1].lower() == 'which'):
        this_chunk.append(('location', 'NO_ENTRY', False))
        this_chunk.append(('place', 'NO_ENTRY', False))
        
    for info_i, info_v in enumerate(this_chunk):
        if info_v[0].lower() == 'who':
            this_chunk[info_i] = ('figure', 'NO_ENTRY', False)
            this_chunk.append(('character', 'NO_ENTRY', False))
            
    if ent_match:
        # TODO: 2 or 1 here?
        special_nouns = re.search(r'(\s[A-Z][A-Za-z]*){2,}\Z', sen.text)
        # e.g. Song of Ice and Fire....
        preposition_dict = {'And': 'and', 'Or': 'or', 'Of': 'of'}
        if special_nouns:
            found_entity = str(special_nouns.group(0))
            for prep in preposition_dict:
                found_entity = re.sub(prep, preposition_dict[prep], found_entity)
            page_py = FIND_WIKI.page(found_entity)
            if page_py.exists():
                this_chunk.append((found_entity, 'RETRIEVED_ENTRY', True))
    
    return this_chunk


def get_features(item):
    '''
    Generate features and key words for processing 
    '''
    key_word = None
    feature_list = []
    for item_v in item: 
        if item_v[2] == True and (item_v[1] in ENTS_TYPE): # maybe I should put more... put them in a list
            # maybe for the key word, find the most suitbale one here.
            key_word = item_v[0]
        else:
            feature_list.append(item_v[0])
    if key_word is None:
        print ('No key words! Guess from a noun chunk instead!')
        for item_v in item: 
            if item_v[2] == True: 
                key_word = item_v[0]
    return key_word, feature_list


def retrieve(ent_page, key_list, n=3, org_sen='', fast_lookup=True, thre=0, vector_model=False):
    '''
    Retrieve the entity page and get the results;

    Return the top n results selected. The format is [('answer', confidence int value)].   
    '''
    
    if not key_list:
        return ("No entities identified! Try better query! ")
    if n < 0:
        print ('Cannot specify a negative number to the number of answers. Print top 1 result instead.')
        n = 1
    
    page = wptools.page(ent_page, silent=True)
    # Parse the page and get the wikidata
    page.get_parse(show=False)
    page.get_wikidata(show=False)
    
    res = []
    key_exact_match = False

    if vector_model:
        print ('Switching to vector large model of Spacy...')
        try:
            nlp = NLP_VEC
        except:
            print ('No vector model found!')
    else: 
        nlp = NLP_CORE
        
    for key in key_list:
        key = nlp(key)
        # build a dict for better search
        data_dict = {}
        if page.data['infobox']:
            for item in page.data['infobox']:
                item_sub = re.sub(r'[^a-zA-Z]', ' ', item)
                if item_sub in org_sen and not key_exact_match:
                    print ('exact same keyword \'{}\' found in infobox!'.format(item))
                    res.append((page.data['infobox'][item], item))
                item_sim = nlp(item_sub).similarity(key)
                if item_sim > thre:
                    data_dict[item] = (item_sim, 'box')

        for item in page.data['wikidata']:
            item_trim = ' '.join(item.split()[:-1])
            if item_trim in org_sen and not key_exact_match:
                print ('exact same keyword \'{}\' found in wikidata!'.format(item))
                res.append((page.data['wikidata'][item], item))
            item_sim = nlp(item_trim).similarity(key)
            if item_sim > thre:
                data_dict[item] = (item_sim, 'wiki')
                
        # if we have already found the exact match (when res[0][1]) is a str)
        if res != [] and type(res[0][1]) == str:
            key_exact_match = True
            res = sorted(res, key=lambda x: len(x[1]), reverse=True)
            res = [(r[0], 1) for r in res]
            # early return because finding 
            if fast_lookup:
                return res[:n]

        
        if not data_dict:
            print ('No information retrieved based on the threshold! Returning all info instead!')
            # can't really use the item here. Sometimes it's an empty dict. No idea why.
            res = (page.data['infobox'], page.data['wikidata'])
            top_confidence = 0.1
            return res, top_confidence

        # rank the dict based on item similarities
        sort_list = sorted(data_dict.items(), key = lambda x : x[1][0], reverse = True)

        # get the first n item of the list
        sort_list = sort_list[:n]
        top_confidence = sort_list[0][1][0]
        # print ('Top confidence level according to similarities is {0:.3f}'.format(top_confidence))

        for i in sort_list:
            dict_key = i[0]
            if i[1][1] == 'box':
                res.append((page.data['infobox'][dict_key], i[1][0]))
                # res.append((dict_key, page.data['infobox'][dict_key], i[1][0], key)) # for debug purpose
            
            if i[1][1] == 'wiki':
                res.append((page.data['wikidata'][dict_key], i[1][0]))
                # res.append((dict_key, page.data['wikidata'][dict_key], i[1][0], key)) # for debug purpose
                
    ranked_res = sorted(res, key=lambda x: x[1], reverse=True)
    return ranked_res[:n]
