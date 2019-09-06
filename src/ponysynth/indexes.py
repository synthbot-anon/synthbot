from typing import *


class Node:
	def __init__(self):
		self.children: List['Node'] = {}
		self.references: List[Any] = set()

I = TypeVar('I')
R = TypeVar('R')

class SubstringIndex:
	# TODO: replace this with Ukkonen's algorithm if needed
	def __init__(self):
		self.root = Node()

	def index(self, keystring: Sequence[I], reference: Sequence[R]):
		reference = tuple(reference)
		
		position = 0
		while keystring:
			self._index_single(keystring, reference, position)
			keystring = keystring[1:]
			position += 1

	def _index_single(self, keystring: Sequence[I], reference: Sequence[R], position: int):
		current_position = self.root
		for keychar in keystring:
			if keychar in current_position.children:
				current_position = current_position.children[keychar]
			else:
				next_position = Node()
				current_position.children[keychar] = next_position
				current_position = next_position
			current_position.references.add((reference, position))

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
