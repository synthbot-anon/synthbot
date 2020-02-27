"""Parse stories marked up in CookieSynth format.

Usage:
    from cookiesynth import CookieSynthNavigator

    parser = CookieSynthParser(labeled_story)
    dialogue_segments = parser.getSegments(required_property="character")

    for d in dialogue_segments:
        print(f'{d['character']}: {d.text}')

This module treats story segments as objects. Properties are assigned to story
segments, not to individual (lexical) characters. Usually when you want to get
a the label for a segment of text, you should NOT work directly with the one
segment you care about. You should find all overlapping labeled segments and
work with those.
"""

import bisect
from collections import namedtuple
from lark import Lark, Visitor
from codecs import encode, decode


COOKIESYNTH_GRAMMAR = """
    start: token*

    token: meta 
         | open_segtype
         | open_segassign
         | close
         | anything
    
    meta.3: "[" _SP? "meta" _SP target (_SP segassign)+ _SP? "]"
    open_segtype.2: "[" _SP? segtype (_SP segassign)* "]"
    open_segassign.2: "[" _SP? segassign _SP? "]"
    close.2: "[/" _SP? KEYWORD _SP? "]"
    anything.1: ANYTHING

    segtype: KEYWORD
    segassign: KEYWORD _SP? "=" _SP? VALUE
    target: KEYWORD _SP? "=" _SP? VALUE

    KEYWORD: /[a-zA-Z][a-zA-Z0-9_]*/
    VALUE: ESCAPED_STRING
    ANYTHING: /([^\\[]+|\\[)/

    _SP: WS
    %ignore _SP

    %import common.ESCAPED_STRING
    %import common.WS
"""

COOKIESYNTH_PARSER = Lark(COOKIESYNTH_GRAMMAR)

Segment = namedtuple("Segment", ["start", "end"])
Assignment = namedtuple("Assignment", ["sprop", "value"])
SType = namedtuple("SType", ["stype"])
TransitionPoint = namedtuple("TransitionPoint", ["start"])

MetaTarget = namedtuple("MetaTarget", ["sprop", "value"])
MetaTransition = namedtuple("MetaTransition", ["metatarget", "assignments"])

# TODO: collapse PendingSType and PendingAssignment into a single class
PendingSegment = namedtuple("PendingSegment", ["start"])
PendingSType = namedtuple("PendingSType", ["segment", "stype", "assignments"])
PendingAssignment = namedtuple("PendingAssignment", ["segment", "assignment"])


def _unescape(s):
    """Unescape strings

    Remove leading and trailing quotes, and unescape characters escaped with a
    backslack.
    """
    assert s[0] == "\"" and s[-1] == "\""
    return decode(encode(s, "latin-1", "backslashreplace"), "unicode-escape")[1:-1]


class CookieSynthTokenizer(Visitor):
    """Parses a CookieSynth-labeled story.

    Parses a story labeled with CookieSynth markup. This markup format treats
    each story segment as an object, and it assigns types and properties to
    those objects. Take the following example:

        "Next time," she declared, as much for her own benefit as it was for
        Spike's. "I wouldn't know where to aim the Telescope yet."

    Every substring in the above text can be treated as an object. Objects
    like:

        "Next time,"

    can be considered of type Dialogue, which we can mark up as:

        [dialogue]"Next time,"[/dialogue]

    They can also have properties, like a speaking character. These can be
    marked up as:

        [character="Twilight Sparkle"]"Next time,"[/character]

    This is conceptually the same as:

        segment = parser.getStorySegment(5017, 5029) # "Next time,"
        segment.character = "Twilight Sparkle"

    As a shorthand, a type and properties can be assigned in the same
    tag.

        [dialogue character="Twilight"]"Next time,"[/dialogue]

    Sometimes it's useful to assign objects, rather than strings, to story
    segment properties. For example:

        twilight = parser.at(0).get("character", "Twilight")
        twilight["voice"] = "nasally contralto scale"
        twilight["color"] = "purple"

    This can be done with the following [meta] tag at the beginning of the
    story (i.e., at position 0):

        [meta character="Twilight" voice="nasally contralto scale" color="purple"]

    Now whenever the parser finds that a story segment was labeled with
    character="Twilight", the string "Twilight" gets replaced with an object
    with character.voice="nasally contralto scale" and character.color="purple".
    The original string value will be retained as the object id.

        segment = parser.getStorySegment(5017, 5029)
        # segment.character.id == "Twilight"
        # segment.character.voice == "nasally contralto scale"

    A [meta] tag begins taking effects at the position where it is declared,
    and it retains its effects until a new [meta] tag overrides the same
    property.

    The markup recognizes the following tags.

    [x]...[/x]
        This is used to assign a type to a story segment. For example, if a
        word should be treated as an onomatopoeia, it can be labeled as:
        [onomatopoeia]bark![/onomatopoeia]

    [x="y"]...[/x]
        This is used to assign a property value to a story segment. For
        example, a segment's "style" property can be labeled as:
        [style="internal monologue"]...[/style]
        [style="exaggerated"]...[/style]

    [x a="b" c="d" ...]...[/x]
        This is a shorthand to assign a type and multiple properties with a
        single tag.

    [meta property="value" c="d" ...]
        By default, all values are treated as string. The meta tags turns
        certain values into objects, and it sets properties on that object.
        For example, this meta tag will treat the character string "rainbow
        dash" as an object and give it a voice value of "raspy":
        [meta character="rainbow dash" voice="raspy" color="blue"]

        After this, whenever [character="rainbow dash"] is used, it is implicitly
        assumed that this character has a raspy voice and a blue color.

        Note that the [meta] tag should not get closed. The effects of a [meta]
        tag remain until a new [meta] tag overrides the same property.
    """

    def __init__(self):
        self.story_pieces = []
        self.current_position = 0
        self.stacks = {}
        self.meta_transitions = {}
        self.assignments = {}
        self.stypes = {}

    def meta(self, tree):
        target = next(tree.find_data("target"))
        target_segprop = target.children[0].value
        target_segvalue = _unescape(target.children[-1].value)
        meta_target = MetaTarget(target_segprop, target_segvalue)

        assignments = []
        for segassign in tree.find_data("segassign"):
            segprop = segassign.children[0].value
            segvalue = _unescape(segassign.children[-1].value)
            assignments.append(Assignment(segprop, segvalue))

        transition_point = TransitionPoint(self.current_position)
        meta_transition = MetaTransition(meta_target, assignments)
        self.meta_transitions[transition_point] = meta_transition

    def open_segtype(self, tree):
        segtype = next(tree.find_data("segtype")).children[0].value
        stype = SType(segtype)

        assignments = []
        for segassign in tree.find_data("segassign"):
            segprop = segassign.children[0].value
            segvalue = _unescape(segassign.children[-1].value)
            assignments.append(Assignment(segprop, segvalue))

        segment = PendingSegment(self.current_position)
        pending = PendingSType(segment, stype, assignments)
        self.stacks.setdefault(segtype, []).append(pending)

    def open_segassign(self, tree):
        segassign = next(tree.find_data("segassign"))
        segprop = segassign.children[0].value
        segvalue = _unescape(segassign.children[-1].value)

        segment = PendingSegment(start=self.current_position)
        assignment = Assignment(segprop, segvalue)
        pending = PendingAssignment(segment, assignment)
        self.stacks.setdefault(segprop, []).append(pending)

    def close(self, tree):
        segtype = tree.children[0].value
        pending = self.stacks[segtype].pop()

        if isinstance(pending, PendingAssignment):
            segment, assignment = _complete_assignment(pending, self.current_position)
            self.assignments.setdefault(segment, []).append(assignment)

        elif isinstance(pending, PendingSType):
            segment, stype, assignments = _complete_stype(
                pending, self.current_position
            )
            self.stypes.setdefault(segment, []).append(stype)
            for assignment in assignments:
                self.assignments.setdefault(segment, []).append(assignment)

        else:
            raise Exception(
                f"invalid closed object: {pending} of type"
                " {type(pending)} on line {self.current_position}"
            )

    def anything(self, tree):
        next_piece = tree.children[0].value
        self.story_pieces.append(next_piece)
        self.current_position += len(next_piece)


def _complete_assignment(pending, end_position):
    start_position = pending.segment.start
    assignment = pending.assignment
    segment = Segment(start=start_position, end=end_position)

    return segment, assignment


def _complete_stype(pending, end_position):
    start_position = pending.segment.start
    stype = pending.stype
    assignments = pending.assignments
    segment = Segment(start=start_position, end=end_position)

    return segment, stype, assignments


class MetaReplay:
    def __init__(self, transitions):
        cached_meta = {0: {}}

        running_state = {}
        for transition_point, transition in transitions.items():
            running_state[transition.metatarget] = transition.assignments
            cached_meta[transition_point.start] = running_state.copy()

        self.cached_meta = sorted(cached_meta.items(), key=lambda x: x[0])
        self.keys = [x[0] for x in self.cached_meta]

    def __getitem__(self, key):
        if isinstance(key, int):
            assert key >= 0

            relevant_meta_index = bisect.bisect_right(self.keys, key)
            if relevant_meta_index:
                return self.cached_meta[relevant_meta_index - 1][1]

        raise IndexError

    def get_value(self, index, segprop, segvalue, relevant_meta=None, known_objects={}):
        if (segprop, segvalue) in known_objects:
            return known_objects[(segprop, segvalue)]

        result = {"id": segvalue}
        known_objects[(segprop, segvalue)] = result

        if relevant_meta == None:
            relevant_meta = self[index]

        meta_target = MetaTarget(segprop, segvalue)
        if meta_target in relevant_meta:
            for assignment in relevant_meta[meta_target]:
                result[assignment.sprop] = self.get_value(
                    index,
                    assignment.sprop,
                    assignment.value,
                    relevant_meta,
                    known_objects,
                )

        return result


class SegmentTopology:
    OVERLAPPING = "overlapping"
    COVERING = "covering"

    def __init__(self, segments, story_length):
        self.by_start = sorted(segments, key=lambda x: x.start)
        self.start_keys = [x.start for x in self.by_start]
        self.by_end = sorted(segments, key=lambda x: x.end)
        self.end_keys = [x.end for x in self.by_end]
        self.story_length = story_length

    def _end_after_inclusive(self, index):
        first = bisect.bisect_left(self.end_keys, index)
        return self.by_end[first:]

    def _start_strictly_before(self, index):
        post_last = bisect.bisect_left(self.start_keys, index)
        if post_last == None:
            return []
        return self.by_start[:post_last]

    def _start_before_inclusive(self, index):
        post_first = bisect.bisect_right(self.start_keys, index)
        if post_first == None:
            return []
        return self.by_start[:post_first]

    def _end_strictly_after(self, index):
        last = bisect.bisect_right(self.end_keys, index)
        return self.by_end[last:]

    def get_overlapping(self, start, end):
        # find overlapping segments that end after this one starts and start before
        # this one ends

        result = set()

        for candidate in self._end_after_inclusive(start):
            if candidate.start >= end:
                break
            result.add(candidate)

        for candidate in self._start_strictly_before(end)[::-1]:
            if candidate.end < start:
                break
            result.add(candidate)

        return result

    def get_covers(self, start, end):
        # TODO: use an rtree to make get_covers() more efficient

        # find covering segments that start before this one start and end after
        # this one ends

        start_before = set(self._start_before_inclusive(start))
        end_after = set(self._end_strictly_after(end))

        print(start_before)
        print(end_after)

        return start_before.intersection(end_after)

    def __getitem__(self, key):
        if isinstance(key, int):
            key = slice(key, key + 1, SegmentTopology.COVERING)

        start, end, _ = slice(key.start, key.stop).indices(self.story_length)
        match_type = key.step

        if match_type == SegmentTopology.OVERLAPPING:
            return self.get_overlapping(start, end)
        elif match_type == SegmentTopology.COVERING:
            return self.get_covers(start, end)

        raise TypeError(
            'match type ("step" value) must be one of OVERLAPPING or COVERING'
        )


class SegmentDict:
    def __init__(self, items_by_seg, story_length):
        self._dict = items_by_seg.copy()
        self.segment_db = SegmentTopology(self._dict.keys(), story_length)

    def __getitem__(self, key):
        result = []
        for matching_segment in self.segment_db[key]:
            result.append((matching_segment, self._dict[matching_segment]))

        return result


class MetaSegmentDict:
    def __init__(self, segment_dict, meta_replay):
        self.segment_dict = segment_dict
        self.meta_replay = meta_replay

    def __getitem__(self, key):
        for segment, assignments in self.segment_dict[key]:
            result = {}
            for assignment in assignments:
                next_prop = self.meta_replay.get_value(
                    segment.start, assignment.sprop, assignment.value
                )
                result[assignment.sprop] = next_prop
            yield result


class CookieSynthNavigator:
    def __init__(self, marked_story):
        tokenizer = CookieSynthTokenizer()
        parse_tree = COOKIESYNTH_PARSER.parse(marked_story)
        tokenizer.visit(parse_tree)
        self.tokenizer = tokenizer

        self.story = "".join(tokenizer.story_pieces)
        self.story_length = len(self.story)
        self.meta = MetaReplay(tokenizer.meta_transitions)
        self.types = SegmentDict(tokenizer.stypes, self.story_length)

        stateless_assignments = SegmentDict(tokenizer.assignments, self.story_length)
        self.assignments = MetaSegmentDict(stateless_assignments, self.meta)
