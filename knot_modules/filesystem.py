import json
from pathlib import Path
from os import listdir
import re
import plugins

@plugins.register
class KnotsStore:
    def __init__(self):
        self.path = Path.home().joinpath(".knots")
        self.textpath = self.path.joinpath("text")
        self.info_file = self.path.joinpath("knots.json")
        self.tree_file = self.path.joinpath("tree.json")
        self.check()

    def type(self):
        return "filesystem"

    def check(self):
        if not Path(self.path).exists():
            Path(self.path).mkdir()

        if not Path(self.textpath).exists():
            Path(self.textpath).mkdir()

    def save_info(self, store):
        f_info = open(str(self.info_file), "w", encoding="utf-8")
        f_info.write("[")

        comma = False
        for key, value in store.items():
            # Write note metainfo
            if comma:
                f_info.write(",")
            f_info.write(str(json.dumps(value, indent=2)))
            comma = True
        f_info.write("]")
        f_info.close()

    def save_text(self, store):
        for key, value in store.items():
            # Write note text
            f_text = open(str(self.textpath.joinpath(str(key) + ".txt")), "w", encoding="utf-8")
            f_text.write(str(value))
            f_text.close()

    def save_tree(self, tree):
        f_info = open(str(self.tree_file), "w", encoding="utf-8")
        f_info.write(str(tree))
        f_info.close()

    def load_tree(self):
        if not self.tree_file.exists():
            return None
        f = open(str(self.tree_file), "r")
        tree = str(f.read())
        f.close()
        return tree

    def load_info(self):
        if not self.info_file.exists():
            return None
        f = open(str(self.info_file), "r")
        notes = str(f.read())
        f.close()
        try:
            notes = json.loads(str(notes))
        except json.decoder.JSONDecodeError as error:
            print(error)

        bank_notes = {}
        for note in notes:
            bank_notes[note['id']] = note
        return bank_notes

    def load_text(self, id):
        f = open(str(self.textpath.joinpath(str(id)+".txt")), "r")
        notes = str(f.read())
        f.close()
        return notes

    def search(self, phrase, regex):
        found_phrases_id = []

        def search_method(str_line):
            if regex:
                return bool(re.match(phrase, str_line))
            else:
                return phrase in str(str_line)

        for eachfile in listdir(self.textpath):
            f_search = open(self.textpath.joinpath(eachfile), "r")

            for line in f_search.readlines():
                if search_method(line):
                    found_phrases_id.append(eachfile.strip(".txt"))
            f_search.close()

        return found_phrases_id