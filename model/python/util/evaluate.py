import csv
import sys
import numpy as np
import json

def evaluate_classifier(classifier, eval_set, batch_size):
    """
    Function to get accuracy and cost of the model, evaluated on a chosen dataset.

    classifier: the model's classfier, it should return genres, logit values, and cost for a given minibatch of the evaluation dataset
    eval_set: the chosen evaluation set, for eg. the dev-set
    batch_size: the size of minibatches.
    """
    correct = 0
    genres, hypotheses, cost = classifier(eval_set)
    cost = cost / batch_size
    full_batch = int(len(eval_set) / batch_size) * batch_size
    hypotheses = np.argmax(hypotheses, axis = 1)
    for i in range(full_batch):
        hypothesis = hypotheses[i]
        if hypothesis == eval_set[i]['label']:
            correct += 1        
    return correct / float(len(eval_set)), cost

def evaluate_classifier_genre(classifier, eval_set, batch_size):
    """
    Function to get accuracy and cost of the model by genre, evaluated on a chosen dataset. It returns a dictionary of accuracies by genre and cost for the full evaluation dataset.
    
    classifier: the model's classfier, it should return genres, logit values, and cost for a given minibatch of the evaluation dataset
    eval_set: the chosen evaluation set, for eg. the dev-set
    batch_size: the size of minibatches.
    """
    genres, hypotheses, cost = classifier(eval_set)
    correct = dict((genre,0) for genre in set(genres))
    count = dict((genre,0) for genre in set(genres))
    cost = cost / batch_size
    full_batch = int(len(eval_set) / batch_size) * batch_size

    for i in range(full_batch):
        hypothesis = hypotheses[i]
        genre = genres[i]
        if hypothesis == eval_set[i]['label']:
            correct[genre] += 1.
        count[genre] += 1.

        if genre != eval_set[i]['genre']:
            print('welp!')

    accuracy = {k: correct[k]/count[k] for k in correct}

    return accuracy, cost

def evaluate_final(restore, classifier, eval_sets, batch_size):
    """
    Function to get percentage accuracy of the model, evaluated on a set of chosen datasets.
    
    restore: a function to restore a stored checkpoint
    classifier: the model's classfier, it should return genres, logit values, and cost for a given minibatch of the evaluation dataset
    eval_set: the chosen evaluation set, for eg. the dev-set
    batch_size: the size of minibatches.
    """
    restore(best=True)
    percentages = []
    length_results = []
    for eval_set in eval_sets:
        bylength_prem = {}
        bylength_hyp = {}
        genres, hypotheses, cost = classifier(eval_set)
        correct = 0
        cost = cost / batch_size
        full_batch = int(len(eval_set) / batch_size) * batch_size

        for i in range(full_batch):
            hypothesis = hypotheses[i]
            
            length_1 = len(eval_set[i]['sentence1'].split())
            length_2 = len(eval_set[i]['sentence2'].split())
            if length_1 not in bylength_prem.keys():
                bylength_prem[length_1] = [0,0]
            if length_2 not in bylength_hyp.keys():
                bylength_hyp[length_2] = [0,0]

            bylength_prem[length_1][1] += 1
            bylength_hyp[length_2][1] += 1

            if hypothesis == eval_set[i]['label']:
                correct += 1  
                bylength_prem[length_1][0] += 1
                bylength_hyp[length_2][0] += 1    
        percentages.append(correct / float(len(eval_set)))  
        length_results.append((bylength_prem, bylength_hyp))
    return percentages, length_results

def evaluate_final_winograd(restore, classifier, eval_sets, batch_size):

    """
    Function to get percentage accuracy of the model, evaluated on a set of chosen datasets.
    
    restore: a function to restore a stored checkpoint
    classifier: the model's classfier, it should return genres, logit values, and cost for a given minibatch of the evaluation dataset
    eval_set: the chosen evaluation set, for eg. the dev-set
    batch_size: the size of minibatches.
    """
    INVERSE_MAP = {
    0: "entailment",
    1: "neutral",
    2: "contradiction"
    }
    f = open("confidence_levels_winograd_devset.jsonl","w")
    restore(best=True)
    percentages = []
    length_results = []
    for eval_set in eval_sets:
        bylength_prem = {}
        bylength_hyp = {}
        genres, hypotheses, cost = classifier(eval_set)
        correct = 0
        cost = cost / batch_size
        full_batch = len(eval_set)
        for i in range(full_batch):
            instance = {}
            instance["pairID"] = eval_set[i]['pairID']
            instance["premise"] = eval_set[i]['sentence1']
            instance["hypothesis"] = eval_set[i]['sentence2']
            instance["gold_label"] = INVERSE_MAP[eval_set[i]['label']]
            instance["entailment_confidence"] = hypotheses[i][0]
            instance["neutral_confidence"] = hypotheses[i][1]
            instance["contradiction_confidence"] = hypotheses[i][2]
            instance = json.dumps(instance)
            f.write(instance)
            f.write("\n")
            hypothesis = np.argmax(hypotheses[i])
            if hypothesis == eval_set[i]['label']:
                correct += 1    
        percentages.append(correct / float(len(eval_set)))  
        f.close()
    return percentages


def predictions_kaggle(classifier, eval_set, batch_size, name):
    """
    Get comma-separated CSV of predictions.
    Output file has two columns: pairID, prediction
    """
    INVERSE_MAP = {
    0: "entailment",
    1: "neutral",
    2: "contradiction"
    }

    hypotheses = classifier(eval_set)
    predictions = []
    
    for i in range(len(eval_set)):
        hypothesis = hypotheses[i]
        prediction = INVERSE_MAP[hypothesis]
        pairID = eval_set[i]["pairID"]  
        predictions.append((pairID, prediction))

    #predictions = sorted(predictions, key=lambda x: int(x[0]))

    f = open( name + '_predictions.csv', 'wb')
    w = csv.writer(f, delimiter = ',')
    w.writerow(['pairID','gold_label'])
    for example in predictions:
        w.writerow(example)
    f.close()
