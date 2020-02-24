import docutils
import time, uuid
from kivy.app import App
from kivy.uix.togglebutton import ToggleButton as button
from kivy.uix.textinput import TextInput as ti

from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.screenmanager import Builder, ScreenManager, Screen, SlideTransition
from kivy.clock import Clock
from kivy.event import EventDispatcher


class Note:
    def __init__(self):
        self._n_id = uuid.uuid4()
        self._n_create_time = time.time()
        self._n_update_time = time.time()
        self._n_title = ""

    def get_id(self):
        return self._n_id

    def set_title(self, name):
        self._n_title = name

    def create(self):
        pass

    def save(self):
        pass

    def bookmark(self):
        pass

    def tag(self):
        pass

    def trash(self):
        pass

    def delete(self):
        pass


class NotesApp(App):
    title = "Notes"

    def __init__(self):
        super().__init__()

    def create_note(self):
        note = Note()
        note_butt = button()
        note_butt.id = str(note.get_id())
        note_butt.group = "Notes"
        self.root.ids.note_bar.add_widget(note_butt)

    def title_entered(self):
        pass
    # Event bind example
    # def on_start(self):
    #     self.root.ids['user_input'].bind(on_text_validate=self.enter_message)
    #
    # def enter_message(self, instance):
    #     pass

if __name__ == "__main__":
    NotesApp().run()
