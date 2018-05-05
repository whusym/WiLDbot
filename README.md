# WiLDbot

Welcome. WiLDbot is a simple chatbot to answer Wikipedia questions using Linked WikiData. It is built upon [spaCy](https://spacy.io/), [Wikipedia-API](https://github.com/martin-majlis/Wikipedia-API), and [wptools](https://github.com/siznax/wptools). 

## Dependencies
* Python 3.6
* spaCy 
(We use spaCy v.2.0.11 and its language models `en_core_web_lg`, and `en_vectors_web_lg` (if you need to use an additional word vector model). Navigate to this page https://spacy.io/models/en to see the instructions for installation. )

## How to use
To start the chatbot, simply type
```
python main.py
```
and you will see the prompts. 

#### Demo
[This YouTube video](https://www.youtube.com/watch?v=E3QR2I2e1vk) is a demo for it.

#### Where can I find more testing questions? 
[This](https://github.com/ag-sc/QALD/blob/master/8/data/wikidata-train-7.json) is a json file of the QALD challenge that contains some sample questions. 

## TODO
Add more rules to cover questions on ordinal numbers, complex phrases, etc.

## License 
MIT
