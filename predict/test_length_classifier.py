#!/usr/bin/env python3.5

from collections import Counter
from pickle import load

from classify_relationship import LengthClassifier, common_ancestor_vector,\
    _pair_picker

with open("population_40000.pickle", "rb") as pickle_file:
    population = load(pickle_file)

classifier = LengthClassifier(population, 200)

tested = Counter()
correct = Counter()
incorrect = Counter()
for node_a, node_b in _pair_picker(population):
    relationship_vector = common_ancestor_vector(population, node_a, node_b)
    relationship = classifier.classify(node_a, node_b)
    if relationship == relationship_vector:
        correct[relationship_vector] += 1
    else:
        incorrect[relationship_vector] += 1
    tested[relationship_vector] += 1
    if sum(tested.values()) == 5000:
        break
    
format_string = "Tested: {}\ncorrect: {}\nincorrect: {}\n fraction correct: {}"
print("Overall performance.")
total_tested = sum(tested.values())
total_correct = sum(correct.values())
total_incorrect = sum(incorrect.values())
print(format_string.format(total_tested, total_correct, total_incorrect,
                           total_correct / total_tested))

for relationship_vector, tested_count in tested.items():
    if tested_count < 25:
        continue
    print("Performance for: {}".format(relationship_vector))
    print(format_string.format(tested_count, correct[relationship_vector],
                               incorrect[relationship_vector],
                               correct[relationship_vector] / tested_count))
    if relationship_vector in classifier._distributions.keys():
        print("{} is in the classifier".format(relationship_vector))
    else:
        print("{} is not in the classifier".format(relationship_vector))
    print()

