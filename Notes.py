# python setup.py build_ext --inplace --embed
# gcc <C_file_from_cython> -I<include_directory> -L<directory_containing_libpython> -l<name_of_libpython_without_lib_on_the_front> -o <output_file_name>
# gcc -Os -fPIC ./cyton/Notes.c -I/usr/include/python3.8 -L/usr/include/ -lpython3.8 -o pro_notes  #Linux
# gcc -Os -fPIC -D MS_WIN64 ./cyton/Notes.c -I/usr/include/python3.8 -L/usr/include/ -lpython3.8 -o pro_notes  #Win

import time, uuid
from anytree import NodeMixin, RenderTree
from inspect import getmembers as gm
from pprint import pprint as pp
from kivy.app import App
from kivy.config import Config
from kivy.atlas import Atlas
from kivy.uix.treeview import TreeViewLabel
from kivy.core.window import Window
from kivy.uix.togglebutton import ToggleButton as button

from kivy.clock import Clock
from kivy.event import EventDispatcher

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'log_level', 'debug')  # string, one of ‘trace’, ‘debug’, ‘info’, ‘warning’, ‘error’ or ‘critical’

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

    def add_tag(self, tag):
        self.tags.append(tag)

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


class ThemeFolders(NodeMixin):  # Add Node feature
    def __init__(self, name, id, parent=None, children=None):
        self.name = name
        self.id = id
        self.parent = parent
        if children:
            self.children = children


class NotesApp(App):
    title = "Notes"
    atlas_path = 'atlas://images/default/default'
    window = Window

    def __init__(self):
        super().__init__()
        self.bank = NoteBank()
        self.current_note = None
        self.current_note_button = None
     #   atlas = Atlas('images/default/default.atlas')

    def build(self):
        self.root.ids.folders_tree.bind(minimum_height=self.root.ids.folders_tree.setter('height'))
        self.root.ids.note_bar.bind(minimum_height=self.root.ids.note_bar.setter('height'))

        self.populate_tree_view(self.root.ids.folders_tree, None, self.tree())
        self.populate_tree_view(self.root.ids.folders_tree, None, self.tree())
        self.populate_tree_view(self.root.ids.folders_tree, None, self.tree())

    def tree(self):
        root = ThemeFolders("root", 0)
        ansible = ThemeFolders("Ansible", 1, parent=root)
        redhat = ThemeFolders("RedHat", 2, parent=root)
        proglang = ThemeFolders("Programming", 30, parent=root)
        go = ThemeFolders("GO", 31, parent=proglang)
        python = ThemeFolders("Python", 32, parent=proglang)
        rust = ThemeFolders("Rust", 33, parent=proglang)
        return root

    def populate_tree_view(self, tree_view, parent, node):
        if parent is None:
            tree_node = tree_view.add_node(TreeViewLabel(text=node.name, is_open=True))
        else:
            tree_node = tree_view.add_node(TreeViewLabel(text=node.name, is_open=True), parent)

        for child_node in node.children:
            self.populate_tree_view(tree_view, tree_node, child_node)

    def create_note(self):
        note = Note()
        note_butt = button()
        note_butt.id = str(note.get_id())
        note_butt.group = "Notes"
    #    self.root.ids.nfsdote_bar.bind(minimum_height=self.root.ids.note_bar.setter('height'))  # for scroll option
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
            self.root.ids.tags.values = []
            self.root.ids.bookmark.disabled = True
            self.root.ids.trash.disabled = True
            self.root.ids.bookmark.state = 'normal'
            self.root.ids.trash.state = 'normal'

        if pos == 'down':
            self.current_note_button = instance
            self.current_note = self.bank.get_note(instance.id)
            self.root.ids.title.text = self.current_note.title
            self.root.ids.code.text = self.current_note.text
            self.root.ids.tags.values = self.current_note.tags
            self.root.ids.tags.text = "tags"
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

            self.root.ids.tags.values = self.current_note.tags
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

    def tag_added(self, text):
        self.current_note.add_tag(str(text))
        self.root.ids.tags.values = self.current_note.tags

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
