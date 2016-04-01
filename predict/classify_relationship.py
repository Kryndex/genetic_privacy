from collections import defaultdict, deque
from itertools import chain, product

from scipy.stats import gamma
import pyximport; pyximport.install()

from common_segments import common_segment_lengths
from population_genomes import generate_genomes_ancestors

class LengthClassifier:
    """
    Classifies based total length of shared segments
    """
    def __init__(self, population, labeled_nodes, genome_generator,
                 recombinator, minimum_segment_length = 0):
        self._distributions = dict()
        distribution_calculated_for = set()
        labeled_founders = set(chain.from_iterable(_founders(labeled)
                                                   for labeled
                                                   in labeled_nodes))
        desired_dist = chain.from_iterable(generation.members
                                           for generation
                                           in population.generations[-3:])
        for node in desired_dist:
            population.clean_genomes()
            if node in distribution_calculated_for:
                continue
            unlabeled_founders = _founders(node)
            all_founders = unlabeled_founders & labeled_founders
            to_fit = None
            length_counts = defaultdict(list)
            for i in range(1000):
                generate_genomes_ancestors(all_founders, genome_generator,
                                           recombinator)
                if to_fit is None:
                    has_genomes = set(filter(lambda x: x.genome is not None,
                                             population.members))
                    to_fit = has_genomes - distribution_calculated_for
                for unlabeled, labeled in product(to_fit, labeled_nodes):
                    length = shared_segment_length_genomes(unlabeled,
                                                           labeled,
                                                           minimum_segment_length)
                    length_counts[unlabeled, labeled].append(length)
            for (unlabeled, labeled), lengths in length_counts.items():
                distribution = gamma(*gamma.fit(lengths))
                self._distributions[(unlabeled, labeled)] = distribution
                distribution_calculated_for.add(unlabeled)
        population.clean_genomes()
            
    def get_probability(self, shared_length, query_node, labeled_node):
        """
        Returns the probability that query_node and labeled_node have total
        shared segment length shared_length
        """
        pass
    
def shared_segment_length_genomes(genome_a, genome_b, minimum_length):
    by_autosome = common_segment_lengths(genome_a, genome_b)
    seg_lengths = filter(lambda x: x >= minimum_length,
                         chain.from_iterable(by_autosome.values()))
    return sum(seg_lengths)
    
def _shared_segment_length(node_a, node_b, minimum_length):
    return shared_segment_length_genomes(node_a.genome, node_b.genome,
                                          minimum_length)

def _founders(node):
    assert node is not None
    nodes = deque([node])
    founders = set()
    while len(nodes) > 0:
        node = deque.pop()
        if node.mother is None:
            assert node.father is None
            founders.add(node)
        else:
            deque.appendleft(node.mother)
            deque.appendleft(node.father)
    return founders
    
