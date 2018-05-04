print ('Welcome to WiLDbot! A simple question-answering chatbot for Wikipedia using Linked wikiData.')

from utils import *
def main():
    while True:
        print ('')
        print ('To abort, press Ctrl-C')
        query_str = input('Please type in your query(case sensitive! Example: who is the wife of Barack Obama?): ')
        top_n = input('Please type in the top number of answers you want(default value 3): ')
        vector_m  = input('Please choose to use a new vector model(type "True" or "False", default "False"): ')
        if not top_n.isnumeric():
            top_n = 3
        else:
            top_n = int(top_n)
        if vector_m.lower() == "True" or vector_m == '1':
            vector_model_ = True
        else:
            vector_model_ = False
        query_sen = pre_process(query_str)
        query = process_sen(query_str)
        query_key, query_feature = get_features(query)
        answer = retrieve(query_key, query_feature, n=top_n, org_sen=query_sen, fast_lookup=True, vector_model=vector_model_)
        print ('The answers and the corresponding confidence levels are: \n\n {} \n '.format(answer))


if __name__ == "__main__":
    main()
