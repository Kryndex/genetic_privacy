from collections import namedtuple
from heapq import nlargest

# import pyximport; pyximport.install()
import numpy as np

from classify_relationship import (LengthClassifier,
                                   shared_segment_length_genomes)
from data_logging import write_log
from util import first_missing_ancestor

ProbabilityData = namedtuple("ProbabilityData", ["start_i", "stop_i",
                                                 "cryptic_start_i",
                                                 "cryptic_stop_i"])
MINIMUM_LABELED_NODES = 5
INF = float("inf")
INF_REPLACE = 1.0

class BayesDeanonymize:
    def __init__(self, population, classifier = None):
        self._population = population
        if classifier is None:
            self._length_classifier = LengthClassifier(population, 1000)
        else:
            self._length_classifier = classifier
        # self.__remove_erroneous_labeled()

    def __remove_erroneous_labeled(self):
        print("Removing erroneous labeled nodes")
        id_map = self._population.id_mapping
        labeled_nodes = [id_map[labeled_node_id] for labeled_node_id
                         in self._length_classifier._labeled_nodes]
        to_remove = set()
        for labeled_node in labeled_nodes:
            missing = first_missing_ancestor(labeled_node)
            if missing < 1:
                to_remove.add(labeled_node._id)
        new_labeled = set(self._length_classifier._labeled_nodes) - to_remove
        print("Removeing {} labeled nodes."
              " New size is {}.".format(len(to_remove), len(new_labeled)))
        self._length_classifier._labeled_nodes = list(new_labeled)
                

    def identify(self, genome, actual_node, ibd_threshold = 5000000):
        node_probabilities = dict() # Probability that a node is a match
        id_map = self._population.id_mapping
        length_classifier = self._length_classifier
        shared_list = []
        for labeled_node_id in length_classifier._labeled_nodes:
            labeled_node = id_map[labeled_node_id]
            s = shared_segment_length_genomes(genome, labeled_node.genome,
                                              ibd_threshold)
            shared_list.append((labeled_node_id, s))

        node_data = dict()
        batch_node_id = []
        batch_labeled_node_id = []
        batch_lengths = []
        batch_cryptic_lengths = []
        # This is done for performance reasons, as appending to this
        # list is the hottest part of the loop.
        append_cryptic = batch_cryptic_lengths.append
        distributions = length_classifier._distributions
        # Set membership testing is faster than dictionary key
        # membership testing, so we use a set.
        distribution_members = set(distributions.keys())
        nodes = (member for member in self._population.members
                 if member.genome is not None)
        for node in nodes:
            node_start_i = len(batch_node_id)
            node_id = node._id
            cryptic_start_i = len(batch_cryptic_lengths)
            for labeled_node_id, shared in shared_list:
                if (node_id, labeled_node_id) not in distribution_members:
                    append_cryptic(shared)
                else:                    
                    batch_node_id.append(node_id)
                    batch_labeled_node_id.append(labeled_node_id)
                    batch_lengths.append(shared)
            cryptic_stop_i = len(batch_cryptic_lengths)
            node_stop_i = len(batch_node_id)
            node_data[node] = ProbabilityData(node_start_i, node_stop_i,
                                              cryptic_start_i, cryptic_stop_i)

        calc_prob = length_classifier.get_batch_probability(batch_lengths,
                                                            batch_node_id,
                                                            batch_labeled_node_id)
        cryptic_prob = length_classifier.get_batch_smoothing(batch_cryptic_lengths)

        # index_data = {node._id: tuple(indices)
        #               for node, indices in node_data.items()}
        # siblings = {node._id for node in get_sibling_group(actual_node)}
        # to_dump = {"actual_node_id": actual_node._id,
        #            "calc_prob": calc_prob,
        #            "cryptic_lengths": batch_cryptic_lengths,
        #            "siblings": siblings,
        #            "index_data": index_data}
        # output_filename = "/media/paul/Fast Storage/optimize_data/{}.pickle".format(actual_node._id)
        # with open(output_filename, "wb") as pickle_file:
        #     dump(to_dump, pickle_file)
        node_probabilities = dict()
        for node, prob_data in node_data.items():
            start_i, stop_i, cryptic_start_i, cryptic_stop_i = prob_data
            if node == actual_node:
                pass
                # import pdb
                # pdb.set_trace()
            node_calc = calc_prob[start_i:stop_i]
            node_cryptic = cryptic_prob[cryptic_start_i:cryptic_stop_i]
            log_prob = (np.sum(np.log(node_calc)) +
                        np.sum(np.log(node_cryptic)))
            node_probabilities[node] = log_prob
        # potential_node = max(node_probabilities.items(),
        #                      key = lambda x: x[1])[0]
        write_log("identify", {"node": actual_node._id,
                               "probs": {node._id: prob
                                         for node, prob
                                         in node_probabilities.items()}})
        potential_nodes = nlargest(8, node_probabilities.items(),
                                   key = lambda x: x[1])
        # common_ancestor = recent_common_ancestor(potential_node, actual_node,
        #                                          population.node_to_generation)
        # print("Actual node and guessed node have a common ancestor {} generations back.".format(common_ancestor[1]))
        # calc_for_pair(potential_node, actual_node, length_classifier, shared_map, id_map, population.node_to_generation)
        # print("Log probability for guessed {}, log probability for actual {}".format(node_probabilities[potential_node], node_probabilities[actual_node]))
        # from random import choice
        # random_node = choice(list(member for member in self._population.members
        #                           if member.genome is not None))
        # calc_for_pair(random_node, actual_node, length_classifier, shared_map, id_map)
        # calc_for_pair(random_node, potential_node, length_classifier, shared_map, id_map)
        # return get_sibling_group(potential_node)
        top, top_log_prob = potential_nodes[0]
        sibling_group = get_sibling_group(top)
        # for node, log_prob in potential_nodes[1:]:
        #     if node in sibling_group:
        #         continue
        #     next_node = node
        #     next_log_prob = log_prob
        #     break
        # else:
        #     next_node, next_log_prob = potential_nodes[1]
                
        # log_ratio  = top_log_prob - next_log_prob
        # log_data = {"actual_node_id": actual_node._id,
        #             "prob_indices": prob_data,
        #             "calc_prob": calc_prob,
        #             "cryptic_prob": cryptic_prob
        #             "sibling_group": [node._id for node in sibling_group]}
        # write_log("run_data", log_data)
        # return (sibling_group, log_ratio)
        # return (sibling_group, log_ratio)
        return (sibling_group, 0)
        # return set(chain.from_iterable(get_sibling_group(potential[0])
        #                                for potential in potential_nodes))

def get_sibling_group(node):
    """
    Returns the set containing node and all its full siblings
    """
    if node.mother is None or node.father is None:
        return set([node])
    return set(node.mother.children).intersection(node.father.children)
