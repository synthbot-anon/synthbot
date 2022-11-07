""" Module docstring
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from abc import ABC
from collections import namedtuple
from queue import PriorityQueue

# each formatted file should be a (original, labels) pair
# endos on (original, labels) should be done by cleanest match
# labels should be a list of (offset, descr) pairs
# endos transform offsets
# descr should be associated with format version

LabeledStory = namedtuple("LabeledStory", ["story", "labels"])
_IterationInfo = namedtuple("_IterationInfo", ["i", "j", "prior_cost", "prev"])


def story_walk(original, modified):
    """ """
    distances = {}
    q = PriorityQueue()

    original_length = len(original)
    modified_length = len(modified)

    cache_misses = 0
    cache_hits = 0

    def distance_bound(i, j):
        """ Upper bound the remaining story distance.

        Every difference in remaining unmatched character will end up
        contributing to the final cost. Use that as a lower bound for
        the remaining distance to the end.
        """
        remaining_orig = original_length - i
        remaining_modified = modified_length - j
        result = abs(remaining_orig - remaining_modified)

        return result

    estimated_cost = (distance_bound(0, 0))
    q.put((estimated_cost, _IterationInfo(i=0, j=0, prior_cost=0, prev=None)))

    while not q.empty():
        _, iteration_info = q.get()
        i, j, prior_cost, _ = iteration_info

        if (i, j) in distances:
            # already visited this square with a lower cost... skip it
            cache_hits += 1
            continue

        cache_misses += 1

        if (cache_misses + cache_hits) % 200 == 0:
            print(cache_misses, cache_hits, i, j, original_length,
                  modified_length)

        if i == original_length and j == modified_length:
            # we reached the end!
            return iteration_info

        distances[(i, j)] = prior_cost

        # check if there's a match
        if i < original_length and j < modified_length and original[
                i] == modified[j]:
            # if there is a match, the diagonal square is as good as
            # this one, and its right/bottom squares will be at least
            # as good as this one's right/bottom squares, so just add
            # that diagonal square
            post_cost = prior_cost
            estimated_cost = post_cost + distance_bound(i + 1, j + 1)
            q.put((
                estimated_cost,
                _IterationInfo(i=i + 1,
                               j=j + 1,
                               prior_cost=post_cost,
                               prev=iteration_info),
            ))
            continue

        # if there's no match, add both right and bottom squares to the queue

        if i < len(original):
            post_cost = prior_cost + 1
            estimated_cost = post_cost + distance_bound(i + 1, j)
            q.put((
                estimated_cost,
                _IterationInfo(i=i + 1,
                               j=j,
                               prior_cost=post_cost,
                               prev=iteration_info),
            ))

        if j < len(modified):
            post_cost = prior_cost + 1
            estimated_cost = post_cost + distance_bound(i, j + 1)
            q.put((
                estimated_cost,
                _IterationInfo(i=i,
                               j=j + 1,
                               prior_cost=post_cost,
                               prev=iteration_info),
            ))

    raise Exception(
        "there's a bug in the story_walk algorithm... the loop should not terminal naturally"
    )


def embed(walk_info, orig_story, modified_story):
    result = [-1] * (len(orig_story) + 1)

    assert walk_info.i == len(orig_story)
    assert walk_info.j == len(modified_story)

    result[walk_info.i] = walk_info.j
    last_target = walk_info.j
    walk_info = walk_info.prev

    while walk_info != None:
        if orig_story[walk_info.i] != modified_story[walk_info.j]:
            result[walk_info.j] = last_target
        else:
            result[walk_info.i] = walk_info.j
            last_target = walk_info.j

        walk_info = walk_info.prev

    return result


def relabel(embedding, old_labels):
    # output should be new_labels
    pass


def morph(labeled_story, new_story):
    # embed, then relabel
    pass


# build a suffix tree over new_story
# greedily tokenize old_story using new_story
#   view the old_story in terms of new_story components
#   note that the boundary between adjacent tokens can shift
#   for each boundary, there's a potential substring match
#   goal: find a minimal *sequence* of substring matches
# equivalent to finding a minimal embedding from subobject embedding candidates
