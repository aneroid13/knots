import docutils
import time, uuid
from inspect import getmembers as gm
from pprint import pprint as pp
from kivy.app import App
from kivy.uix.togglebutton import ToggleButton as button
from kivy.uix.textinput import TextInput as ti

from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.screenmanager import Builder, ScreenManager, Screen, SlideTransition
from kivy.clock import Clock
from kivy.event import EventDispatcher


class Note:
    def __init__(self):
        self.uid = uuid.uuid4()
        self.create_time = time.time()
        self.update_time = time.time()
        self.title = ""
        self.tags = []
        self.bookmarked = False
        self.trashed = False

    def get_id(self):
        return self.uid

    # def create(self):
    #     pass
    #
    # def save(self):
    #     pass


class NoteBank:
    def __init__(self):
        self.bank = []

    def add_note(self, note):
        self.bank.append(note)
        return note.uid

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
            if str(child.id) == str(self.current_note.uid):
                self.current_note_button = child

    def button_selection(self, instance, pos):
        if pos is 'normal' and \
                   str(instance.id) == str(self.current_note_button.id):
            self.current_note_button = None
            self.current_note = None

        if pos is 'down':
            self.current_note_button = instance
            #TODO: get note

    def create_new_note(self):
        if self.root.ids.title.text == "" and not self.current_note:
            self.current_note = Note()

            note_butt = button()
            note_butt.id = str(self.current_note.uid)
            note_butt.state = 'down'
            note_butt.group = "Notes"
            note_butt.bind(state=self.button_selection)
            self.root.ids.note_bar.add_widget(note_butt)
            self.find_current_button()

    def title_entered(self):
        if self.root.ids.title.text:
            self.current_note_button.text = self.root.ids.title.text


    # Event bind example
    # def on_start(self):
    #     self.root.ids['user_input'].bind(on_text_validate=self.enter_message)
    #
    # def enter_message(self, instance):
    #     pass

if __name__ == "__main__":
    NotesApp().run()
