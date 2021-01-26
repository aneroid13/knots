import shelve
from pathlib import Path
import plugins

@plugins.register
class KnotsStore:
    def __init__(self):
        self.path = Path.home().joinpath(".knots")
        self.shelf_file = self.path.joinpath("knotes.shf")
        self.check()

    def type(self):
        return "shelf"

    def check(self): pass

    def save_info(self, store):
        shelf = shelve.open(self.shelf_file.as_posix())
        shelf['info'] = store
        shelf.close()

    def save_text(self, store):
        shelf = shelve.open(self.shelf_file.as_posix())
        if 'text' in shelf:
            text = shelf['text']
            text.update(store)
            shelf['text'] = text
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
            return shelf['text'][id]
        else:
            return None

    def search(self, phrase): pass
