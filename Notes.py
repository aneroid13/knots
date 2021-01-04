# python setup.py build_ext --inplace --embed
# gcc <C_file_from_cython> -I<include_directory> -L<directory_containing_libpython> -l<name_of_libpython_without_lib_on_the_front> -o <output_file_name>
# gcc -Os -fPIC ./cyton/Notes.c -I/usr/include/python3.8 -L/usr/include/ -lpython3.8 -o pro_notes  #Linux
# gcc -Os -fPIC -D MS_WIN64 ./cyton/Notes.c -I/usr/include/python3.8 -L/usr/include/ -lpython3.8 -o pro_notes  #Win

import time, uuid, anytree
from anytree.importer import JsonImporter as TreeImporter
from anytree.exporter import JsonExporter as TreeExporter
from inspect import getmembers as gm
from pprint import pprint as pp
from functools import partial
from kivy.app import App
from kivy.config import Config
from kivy.atlas import Atlas
from kivy.uix.treeview import TreeViewLabel, TreeViewNode
from kivy.core.window import Window
from kivy.uix.togglebutton import ToggleButton as button, Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from modules.filesystem import KnotsStore   #importlib

from kivy.clock import Clock
from kivy.event import EventDispatcher

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'log_level', 'warning')  # string, one of ‘trace’, ‘debug’, ‘info’, ‘warning’, ‘error’ or ‘critical’


class NoteInfo:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.create_time = time.time()
        self.update_time = time.time()
        self.title = ""
    #    self.text = ""
        self.codetype = ""
        self.tags = []
        self.folder_id = None
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
        self.info_bank = {}
        self.text_bank = {}
        self.storemetod = KnotsStore()

    def add_noteinfo(self, note):
        self.info_bank[note.id] = note
        return note.id

    def get_noteinfo(self, id: str):
        return self.info_bank[str(id)]

    def add_notetext(self, id: str, text: str):
        self.text_bank[id] = text

    def get_notetext(self, id: str):
        if id not in self.text_bank:
            self.text_bank[id] = self.storemetod.load_text(id)
        return self.text_bank[str(id)]

    def get_notes_by_folder(self, folder_id: str):
        folder_notes = []
        for note in self.info_bank.values():
            if note.folder_id == folder_id:
                folder_notes.append(note)
        return folder_notes

    def save_notes_text(self):
        self.storemetod.save_text(self.text_bank)

    def save_notes_info(self):
        self.storemetod.save_info(self.info_bank)

    def save_tree(self, tree):
        self.storemetod.save_tree(tree)

    def load_notes_info(self):
        return self.storemetod.load_info()

    def load_tree(self):
        return self.storemetod.load_tree()


class Storage:
    def __init__(self, Name, Type):
        self.name = Name
        self.id = uuid.uuid4().hex
        self.type = Type
        if NoteBank().load_tree():
            data = NoteBank().load_tree()
            self.root_folder = TreeImporter().import_(data)
        else:
            self.root_folder = ThemeFolders(self.name)


class ThemeFolders(anytree.NodeMixin):  # Add Node feature
    def __init__(self, name, parent=None, children=None):
        self.name = name
        self.id = str(uuid.uuid4())
        self.parent = parent
        if children:
            self.children = children


class TreeView_LabelButt(BoxLayout, TreeViewNode):
    def __init__(self, msg, **kwargs):
        super(TreeView_LabelButt, self).__init__(**kwargs)
        self.label = Label()
        self.label.text = msg
        self.butt = Button()
        self.add_widget(self.label)
        self.add_widget(self.butt)


class TreeView_Folder(TreeViewLabel):
    def __init__(self, folder_id, **kwargs):
        self.folder_id = folder_id
        super(TreeView_Folder, self).__init__(**kwargs)


class TreeView_NewFolderInput(BoxLayout, TreeViewNode):
    def __init__(self, msg, treenode=None, rename=False, **kwargs):
        super(TreeView_NewFolderInput, self).__init__(**kwargs)
        self.associated_treenode = treenode
        self.height = 32
        self.txtinp = TextInput(text=msg, multiline=False)
        if not rename:
            self.txtinp.bind(on_text_validate=self.add_new_folder)
            self.txtinp.bind(on_focus=self.add_new_folder)
        else:
            self.txtinp.bind(on_text_validate=partial(self.rename_folder, folder_id=treenode.folder_id))
            self.txtinp.bind(on_focus=partial(self.rename_folder, folder_id=treenode.folder_id))
        self.add_widget(self.txtinp)

    def add_new_folder(self, txt_item):
        parent_folder = super().parent_node
        Notes.add_entered_folder(parent_folder, txt_item.text)
        Notes.remove_textinput(self)

    def rename_folder(self, txt_item, folder_id):
        self.associated_treenode.text = self.txtinp.text
        Notes.rename_entered_folder(txt_item.text, folder_id)
        Notes.remove_textinput(self)


class NotesApp(App):
    title = "Notes"
    atlas_path = 'atlas://images/default/default'
    #   atlas = Atlas('images/default/default.atlas')
    window = Window

    def __init__(self):
        super().__init__()
        self.bank = NoteBank()
        self.current_folder_id = '0'
        self.current_note = None
        self.current_text = None
        self.current_note_button = None
        default_storage = Storage("MyStorage", "text")
        self.storages = [default_storage]

    def build(self):
        self.root.ids.folders_tree.bind(minimum_height=self.root.ids.folders_tree.setter('height'))
        self.root.ids.note_bar.bind(minimum_height=self.root.ids.note_bar.setter('height'))

        for each in self.storages:
            self.populate_tree_view(self.root.ids.folders_tree, None, each.root_folder)

    def add_entered_folder(self, parent, folder_name):
        for stor in self.storages:
            if stor.name == "MyStorage":
                storage = stor
        parent_folder = anytree.find_by_attr(storage.root_folder, name="id", value=parent.folder_id)
        current_folder = ThemeFolders(folder_name, parent=parent_folder)

        self.populate_tree_view(self.root.ids.folders_tree, parent, current_folder)

    def rename_entered_folder(self, folder_name, folder_id):
        for stor in self.storages:
            if stor.name == "MyStorage":
                storage = stor
        current_folder = anytree.find_by_attr(storage.root_folder, name="id", value=folder_id)
        current_folder.name = folder_name

    def remove_textinput(self, treenode):
        self.root.ids.folders_tree.remove_node(treenode)

    def populate_tree_view(self, tree_view, parent, node):
        if parent is None:
            tree_node = tree_view.add_node(TreeView_Folder(folder_id=node.id, text=node.name, is_open=True))
        else:
            tree_node = tree_view.add_node(TreeView_Folder(folder_id=node.id, text=node.name, is_open=True), parent)

        for child_node in node.children:
            self.populate_tree_view(tree_view, tree_node, child_node)

    def find_current_button(self):
        for child in self.root.ids.note_bar.children:
            if str(child.id) == str(self.current_note.id):
                self.current_note_button = child

    def init_notes_widgets(self):
        if not self.current_note:
            self.root.ids.title.text = ""
            self.root.ids.code.text = ""
            self.root.ids.tags.values = []
            self.root.ids.bookmark.disabled = True
            self.root.ids.trash.disabled = True
            self.root.ids.bookmark.state = 'normal'
            self.root.ids.trash.state = 'normal'
        else:
            self.root.ids.title.text = self.current_note.title
            self.root.ids.code.text = self.current_text
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

    def button_selection(self, instance, pos):
        if pos == 'normal' and \
           str(instance.id) == str(self.current_note_button.id):  # TODO: fix broken: crash on click
            self.bank.add_noteinfo(self.current_note)
            self.bank.add_notetext(self.current_note.id, self.current_text)
            self.current_note_button = None
            self.current_note = None
            self.current_text = None
        if pos == 'down':
            self.current_note_button = instance
            self.current_note = self.bank.get_noteinfo(instance.id)
            self.current_text = self.bank.get_notetext(instance.id)

        self.init_notes_widgets()

    def create_new_note(self):
        self.current_note = NoteInfo()
        self.current_text = ""
        self.current_note.folder_id = self.current_folder_id
        self.add_note_on_bar(self.current_note.id, "", True)
        self.find_current_button()

        self.root.ids.tags.values = self.current_note.tags
        self.root.ids.bookmark.disabled = False
        self.root.ids.trash.disabled = False
        self.root.ids.bookmark.state = 'normal'
        self.root.ids.trash.state = 'normal'

    def add_note_on_bar(self, note_id, note_title, current):
        note_butt = button()
        note_butt.id = str(note_id)
        note_butt.text = note_title
        note_butt.group = "Notes"
        note_butt.halign = "left"
        note_butt.valign = "top"
        note_butt.shorten = True
        note_butt.shorten_from = "right"
        note_butt.text_size = (180, None)
        if current:
            note_butt.state = 'down'
        note_butt.bind(state=self.button_selection)
        self.root.ids.note_bar.add_widget(note_butt)

    def kv_title_focused(self, focused):
        if focused:
            # Create new note and button
            if self.root.ids.title.text == "" and not self.current_note_button:
                self.create_new_note()
        else:
            # Remove if empty
            if self.current_note_button and not self.root.ids.title.text:
                self.root.ids.note_bar.remove_widget(self.current_note_button)
                self.current_note_button = None
                self.current_note = None
                self.current_text = None

    def kv_bookmarked(self):
        self.current_note.KV_bookmarked()

    def kv_trashed(self):
        self.current_note.KV_trashed()

    def kv_tag_added(self, text):
        self.current_note.add_tag(str(text))
        self.root.ids.tags.values = self.current_note.tags

    def kv_title_entered(self):
        if self.root.ids.title.text:
            self.current_note.title = self.root.ids.title.text
            self.current_note_button.text = self.root.ids.title.text
            self.current_note.update_time = time.time()

    def kv_code_entered(self):
        if self.current_note:
            self.current_text = self.root.ids.code.text
            self.current_note.update_time = time.time()

    def kv_search_entered(self):
        for butt in self.root.ids.note_bar.children:
            if self.root.ids.search.text not in butt.text:
                butt.opacity = 0.2
                butt.disable = True
            else:
                butt.opacity = 1
                butt.disable = False

    def kv_tree_selected(self, treenode_id):
        if self.current_note:
            self.bank.add_noteinfo(self.current_note)
            self.bank.add_notetext(self.current_note.id, self.current_text)
            self.current_note = None
            self.current_text = None
            self.current_note_button = None
            self.init_notes_widgets()

        self.current_folder_id = str(treenode_id)
        self.root.ids.note_bar.clear_widgets()  # clear note_bar
        for note in self.bank.get_notes_by_folder(self.current_folder_id):  # fill note_bar
            self.add_note_on_bar(note.id, note.title, False)

    def kv_button_add_folder(self, treenode):
        self.root.ids.folders_tree.add_node(TreeView_NewFolderInput("New folder"), parent=treenode)

    def kv_button_rename_folder(self, treenode):
        self.root.ids.folders_tree.add_node(TreeView_NewFolderInput(treenode.text, treenode=treenode, rename=True))

    def kv_button_test(self):
 #       self.bank.save_notes_info()
#        self.bank.save_notes_text()
        for stor in self.storages:
            if stor.name == "MyStorage":
                exp = TreeExporter(indent=2, sort_keys=True)
                self.bank.save_tree(exp.export(stor.root_folder))

#TODO:  1. on exit save note to bank
#       2. save bank to file
#       3. Autosave by idle time

if __name__ == "__main__":
    Notes = NotesApp()
    Notes.run()
