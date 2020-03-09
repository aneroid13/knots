# python setup.py build_ext --inplace --embed
# gcc <C_file_from_cython> -I<include_directory> -L<directory_containing_libpython> -l<name_of_libpython_without_lib_on_the_front> -o <output_file_name>
# gcc -Os -fPIC ./cyton/Notes.c -I/usr/include/python3.8 -L/usr/include/ -lpython3.8 -o pro_notes  #Linux
# gcc -Os -fPIC -D MS_WIN64 ./cyton/Notes.c -I/usr/include/python3.8 -L/usr/include/ -lpython3.8 -o pro_notes  #Win

import time, uuid
from inspect import getmembers as gm
from pprint import pprint as pp
from kivy.app import App
from kivy.uix.togglebutton import ToggleButton as button

from kivy.clock import Clock
from kivy.event import EventDispatcher


class Note:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.create_time = time.time()
        self.update_time = time.time()
        self.title = ""
        self.text = ""
        self.tags = []
        self.bookmark = False
        self.trash = False

    def get_id(self):
        return self.id

    def bookmarked(self):
        self.bookmark = not self.bookmark

    def trashed(self):
        self.trash = not self.trash


class NoteBank:
    def __init__(self):
        self.bank = {}

    def add_note(self, note):
        self.bank[note.id] = note
        return note.id

    def get_note(self, id):
        return self.bank[str(id)]

    def update_note(self):
        pass

class NotesApp(App):
    title = "Notes"

    def __init__(self):
        super().__init__()
        self.bank = NoteBank()
        self.current_note = None
        self.current_note_button = None

    def create_note(self):
        note = Note()
        note_butt = button()
        note_butt.id = str(note.get_id())
        note_butt.group = "Notes"
        self.root.ids.note_bar.add_widget(note_butt)

    def find_current_button(self):
        for child in self.root.ids.note_bar.children:
            if str(child.id) == str(self.current_note.id):
                self.current_note_button = child

    def button_selection(self, instance, pos):
        if pos == 'normal' and \
           str(instance.id) == str(self.current_note_button.id):
            self.bank.add_note(self.current_note)
            self.current_note_button = None
            self.current_note = None
            self.root.ids.title.text = ""
            self.root.ids.code.text = ""
            self.root.ids.bookmark.disabled = True
            self.root.ids.trash.disabled = True
            self.root.ids.bookmark.state = 'normal'
            self.root.ids.trash.state = 'normal'

        if pos == 'down':
            self.current_note_button = instance
            self.current_note = self.bank.get_note(instance.id)
            self.root.ids.title.text = self.current_note.title
            self.root.ids.code.text = self.current_note.text
            self.root.ids.bookmark.disabled = False
            self.root.ids.trash.disabled = False
            if self.current_note.bookmark:
                self.root.ids.bookmark.state = 'down'
            else:
                self.root.ids.bookmark.state = 'normal'
            if self.current_note.trash:
                self.root.ids.trash.state = 'down'
            else:
                self.root.ids.trash.state = 'normal'

    def create_new_note(self):
            self.current_note = Note()
            note_butt = button()
            note_butt.id = self.current_note.id
            note_butt.state = 'down'
            note_butt.group = "Notes"
            note_butt.halign = "left"
            note_butt.valign = "top"
            note_butt.shorten = True

            note_butt.shorten_from = "right"
            note_butt.text_size = (180, None)
            note_butt.bind(state=self.button_selection)
            self.root.ids.note_bar.add_widget(note_butt)
            self.find_current_button()

            self.root.ids.bookmark.disabled = False
            self.root.ids.trash.disabled = False
            self.root.ids.bookmark.state = 'normal'
            self.root.ids.trash.state = 'normal'

    def title_focused(self):
        if self.root.ids.title.focused:
            # Create new note and button
            if self.root.ids.title.text == "" and not self.current_note_button:
                self.create_new_note()
        else:
            # Remove if empty
            if self.current_note_button and not self.root.ids.title.text:
                self.root.ids.note_bar.remove_widget(self.current_note_button)
                self.current_note_button = None
                self.current_note = None

    def bookmarked(self):
        self.current_note.bookmarked()

    def trashed(self):
        self.current_note.trashed()

    def title_entered(self):
        if self.root.ids.title.text:
            self.current_note.title = self.root.ids.title.text
            self.current_note_button.text = self.root.ids.title.text

    def code_entered(self):
        if self.current_note:
            self.current_note.text = self.root.ids.code.text


#TODO:  1. on exit save note to bank
#       2. save bank to file

if __name__ == "__main__":
    NotesApp().run()
