import json
from pathlib import Path

class KnotsStore:
    def __init__(self):
        self.path = Path.home().joinpath(".knots")
        self.textpath = self.path.joinpath("text")
        self.info_file = self.path.joinpath("notes.json")
        self.check()

    def check(self):
        if not Path(self.path).exists():
            Path(self.path).mkdir()

        if not Path(self.textpath).exists():
            Path(self.textpath).mkdir()

    def save_info(self, store):
        f_info = open(str(self.info_file), "a")
        f_info.write("[")

        for key, value in store.items():
            # Write note metainfo
            f_info.write(str(json.dumps(value.__dict__, indent=2)))
            f_info.write(",")

        f_info.write("]")
        f_info.close()

    def save_text(self, store):
        for key, value in store.items():
            # Write note text
            f_text = open(str(self.textpath.joinpath(str(key) + ".txt")), "w")
            f_text.write(str(value))
            f_text.close()

    def load_info(self):
        f = open(str(self.info_file), "r")
        notes = str(f.read())
        f.close()
        notes = json.loads(str(notes))
        return notes

    def load_text(self, id):
        f = open(str(self.textpath.joinpath(str(id).join(".txt"))), "r")
        notes = str(f.read())
        f.close()
        return notes

    def search(self, phrase):
        pass
        # return id[]