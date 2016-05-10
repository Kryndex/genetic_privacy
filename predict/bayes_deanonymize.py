from functools import reduce
from operator import mul

import pyximport; pyximport.install()

from classify_relationship import (LengthClassifier,
                                   shared_segment_length_genomes)
MINIMUM_LABELED_NODES = 5

class BayesDeanonymize:
    def __init__(self, population, classifier = None):
        self._population = population
        if classifier is None:
            self._length_classifier = LengthClassifier(population, 1000)
        else:
            self._length_classifier = classifier

    def _compare_genome_node(self, node, genome, cache):
        probabilities = []
        length_classifier = self._length_classifier
        for labeled_node in length_classifier._labeled_nodes:
            if (node, labeled_node) not in length_classifier:
                continue
            if labeled_node in cache:
                shared = cache[labeled_node]
            else:
                shared = shared_segment_length_genomes(genome,
                                                       labeled_node.genome,
                                                       0)
                cache[labeled_node] = shared
                
            prob = length_classifier.get_probability(shared, node,
                                                     labeled_node)
                
            probabilities.append(prob)
            
        return list(filter(lambda x: x is not None, probabilities))

        
    def identify(self, genome):
        node_probabilities = dict() # Probability that a node is a match
        shared_genome_cache = dict()
        for member in self._population.members:
            if member.genome is None:
                continue
            probabilities = self._compare_genome_node(member, genome,
                                                      shared_genome_cache)
            if len(probabilities) < MINIMUM_LABELED_NODES:
                # We don't want to base our estimation on datapoints
                # from too few labeled nodes.
                continue
            node_probabilities[member] = reduce(mul, probabilities, 1)
        potential_node = max(node_probabilities.items(),
                             key = lambda x: x[1])[0]
        return get_sibling_group(potential_node)

def get_sibling_group(node):
    """
    Returns the set containing node and all its full siblings
    Will need to change when monogamy assumptions change.
    """
    return node.mother.children
