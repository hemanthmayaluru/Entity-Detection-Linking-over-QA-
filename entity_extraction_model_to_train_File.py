from __future__ import unicode_literals, print_function

import random
from pathlib import Path
import spacy
#from entity_extraction import generateTrainingData
from tqdm import tqdm # loading bar
from spacy.gold import GoldParse
from spacy.util import minibatch, compounding
from spacy.scorer import Scorer
import ast

#-----------------------------------------Function Definitions------------------------------------
# Train and Test Data Parsing and Loading
def load_data(file_path):
    data = []
    with open(file_path, 'r', encoding = 'utf-8') as f:
        for line in f:
            data.append(line)
        f.close()
    return data

# Function to get the text(questions in our case) and their entities
def get_text_annotations(elem):
    if '\',' in elem:
        elem_split = elem.split('\',')
    if '\",' in elem:
        elem_split = elem.split('\",')
    text = elem_split[0][1:].strip()
    annotations = elem_split[1][:-2].strip()
    if annotations[-1] == ')':
        annotations = annotations[:-1]
    annotations = ast.literal_eval(annotations)
    return text,annotations
	
# Model Evaluation
def evaluate(output_dir, data):
    scorer = Scorer()
    for text, annotations in data:
        #text, annotations = get_text_annotations(elem)
        doc_gold_text = output_dir.make_doc(text)
        gold = GoldParse(doc_gold_text, annotations.get('entities'))
        pred_value = output_dir(text)
        scorer.score(pred_value, gold)
    return scorer.scores

#-----------------------------------------Data Processing & Model Creation------------------------------------
#Loading train and test data sets
#train_data = load_data('train_data_new.txt')
#test_data = load_data('test_data_new.txt')




# Define our variables
model = None
output_dir=Path("D:\\New folder\\NLP\\outputModel")
n_iter=100

if model is not None:
    nlp = spacy.load(model)  # load existing spaCy model
    print("Loaded model '%s'" % model)
else:
    nlp = spacy.blank('en')  # create blank Language class
    print("Created blank 'en' model")

# create the built-in pipeline components and add them to the pipeline
if 'ner' not in nlp.pipe_names:
    ner = nlp.create_pipe('ner')
    nlp.add_pipe(ner, last=True)
# otherwise, get it so we can add labels
else:
    ner = nlp.get_pipe('ner')
# add labels
for _, annotations in TRAIN_DATA:
    #_,annotations = get_text_annotations(elem)
    for ent in annotations.get('entities'):
        ner.add_label(ent[2])
print('Creating Model...')
# get names of other pipes to disable them during training
other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
with nlp.disable_pipes(*other_pipes):  # only train NER
    optimizer = nlp.begin_training()
    for itn in range(n_iter):
        random.shuffle(TRAIN_DATA)
        losses = {}
        # batch up the examples using spaCy's minibatch
        batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
        for batch in batches:
            text, annotations = zip(*batch)
            nlp.update(
                text,  # batch of texts
                annotations,  # batch of annotations
                drop=0.5,  # dropout - make it harder to memorise data
                losses=losses,
			)
        print("Losses:",losses)
print('Model Created Successfully !!!')
print('Testing Model on Train Data...')

# test the trained model
with open("train_model_testing.txt", "w", encoding = 'utf-8') as train_file:
    for text, _ in TRAIN_DATA:
        doc = nlp(text)
        #print('Entities Train', [(ent.text, ent.label_) for ent in doc.ents])
        #print('Tokens Train', [(t.text, t.ent_type_, t.ent_iob) for t in doc])
        train_file.write('\n')
        train_file.write('Entities:')
        train_file.write(str([(ent.text, ent.label_) for ent in doc.ents]))
        train_file.write('\n')
        train_file.write('Tokens')
        train_file.write(str([(t.text, t.ent_type_, t.ent_iob) for t in doc]))
    train_file.close()
print('Model Tested Succesfully on Train Data !!!')

# save model to output directory
print('Saving Model...')
if output_dir is not None:
    output_dir = Path(output_dir)
    if not output_dir.exists():
        output_dir.mkdir()
    nlp.to_disk(output_dir)
    print("Saved model to", output_dir)

# test the saved model
print('Testing Model on Test Data...')
print("Loading from", output_dir)
nlp2 = spacy.load(output_dir)
fail_cases = 0
pass_cases = 0
no_label = 0
with open("test_model_testing.txt", "w", encoding = 'utf-8') as test_file:
    for text, _ in TEST_DATA:
        doc = nlp2(text)
        #text,_ = get_text_annotations(elem)
        #print('Entities Test', [(ent.text, ent.label_) for ent in doc.ents])
        #print('Tokens Test', [(t.text, t.ent_type_, t.ent_iob) for t in doc])
        test_file.write('\n')
        test_file.write('Entities:')
        test_file.write(str([(ent.text, ent.label_) for ent in doc.ents]))
        test_file.write('\n')
        test_file.write('Tokens')
        test_file.write(str([(t.text, t.ent_type_, t.ent_iob) for t in doc]))
    test_file.close()
print('Model Tested Succesfully on Test Data !!!')
print('Evaluating model...')
accuracy_train_data = evaluate(nlp2, TRAIN_DATA)
accuracy_test_data = evaluate(nlp2, TEST_DATA)
print('--------Final Accuracy--------')
print('Training Accuracy: \n', accuracy_train_data)
print('\n')
print('Testing Accuracy: \n', accuracy_test_data)