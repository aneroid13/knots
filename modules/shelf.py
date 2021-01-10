import json
import shelve
from pathlib import Path
from inspect import getmembers as gm
from pprint import pprint as pp

class KnotsStore:
    def __init__(self):
        self.path = Path.home().joinpath(".knots")
        self.shelf_file = self.path.joinpath("notes.shf")
    #    self.textpath = self.path.joinpath("text.shf")
    #    self.tree_file = self.path.joinpath("tree.shf")
        self.check()

    def check(self): pass

    def save_info(self, store):
        shelf = shelve.open(self.shelf_file.as_posix())
        shelf['info'] = store
        shelf.close()

    def save_text(self, store):
        shelf = shelve.open(self.shelf_file.as_posix())
        if 'text' in shelf:
            shelf['text'].update(store)
        else:
            shelf['text'] = store
        shelf.close()

    def save_tree(self, tree):
        shelf = shelve.open(self.shelf_file.as_posix())
        shelf['tree'] = tree
        shelf.close()

    def load_tree(self):
        shelf = shelve.open(self.shelf_file.as_posix())
        if 'tree' in shelf:
            return shelf['tree']
        else:
            return None

    def load_info(self):
        shelf = shelve.open(self.shelf_file.as_posix())
        if 'info' in shelf:
            return shelf['info']
        else:
            return None

    def load_text(self, id):
        shelf = shelve.open(self.shelf_file.as_posix())
        if 'text' in shelf:
            return shelf['text']
        else:
            return None

    def search(self, phrase): pass
