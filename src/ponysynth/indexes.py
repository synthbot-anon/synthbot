from typing import *
import itertools


class Node:
	def __init__(self):
		self.children: List['Node'] = {}
		self.references: List[Any] = []

I = TypeVar('I') # index type used for search terms
R = TypeVar('R') # reference type used for results

class SubstringIndex:
	# TODO: replace this with Ukkonen's algorithm if needed
	def __init__(self):
		self.root = Node()

	def index(self, keystring: Sequence[I], reference: R):
		position = 0
		while keystring:
			self._index_single(keystring, reference, position)
			keystring = keystring[1:]
			position += 1

	def _index_single(self, keystring: Sequence[I], reference: R, position: int):
		current_position = self.root
		for keychar in keystring:
			if keychar in current_position.children:
				current_position = current_position.children[keychar]
			else:
				next_position = Node()
				current_position.children[keychar] = next_position
				current_position = next_position
			current_position.references.append((reference, position))

	def find(self, substr: Sequence[I]):
		substr = tuple(substr)
		current_position = self.root
		for keychar in substr:
			if keychar in current_position.children:
				current_position = current_position.children[keychar]
			else:
				next_position = Node()
				current_position.children[keychar] = next_position
				current_position = next_position
		return current_position.references

	def read_layer(self, height):
		return self.read_sublayer(height, self.root)

	def read_sublayer(self, descend, parent):
		if descend == 0:
			return (x for x in parent.references)

		generators = []
		for child in parent.children.values():
			subgen = self.read_sublayer(descend - 1, child)
			generators.append(subgen)

		return itertools.chain(*generators)


