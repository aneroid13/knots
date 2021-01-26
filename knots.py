# python setup.py build_ext --inplace --embed
# gcc <C_file_from_cython> -I<include_directory> -L<directory_containing_libpython> -l<name_of_libpython_without_lib_on_the_front> -o <output_file_name>
# gcc -Os -fPIC ./cyton/knots.c -I/usr/include/python3.8 -L/usr/include/ -lpython3.8 -o knots  #Linux
# gcc -Os -fPIC -D MS_WIN64 ./cyton/knots.c -I/usr/include/python3.8 -L/usr/include/ -lpython3.8 -o knots  #Win

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
from kivy.clock import Clock
from kivy.event import EventDispatcher

import knot_modules

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'log_level', 'warning')  # string, one of ‘trace’, ‘debug’, ‘info’, ‘warning’, ‘error’ or ‘critical’


class NoteInfo:
    def __init__(self):
        self.button = None
        self.text = ""
        self.note = {
                'id': str(uuid.uuid4()),
                'create_time': time.time(),
                'update_time': time.time(),
                'title': "",
                'codetype': "",
                'tags': [],
                'folder_id': None,
                'bookmark': False,
                'trash': False,
                }

    def new(self):
        self.__init__()

    def set_button(self, butt):
        self.button = butt

    def get_id(self):
        return self.note['id']

    def get_bookmark(self):
        return self.note['bookmark']

    def bookmarked(self):
        self.note['bookmark'] = not self.note['bookmark']

    def get_trash(self):
        return self.note['trash']

    def trashed(self):
        self.note['trash'] = not self.note['trash']

    def add_tag(self, tag):
        self.note['tags'].append(tag)

    def update_time(self):
        self.note['update_time'] = time.time()


class NoteBank:
    def __init__(self, type):
        self.storemetod = knot_modules.storage(plugin=type)

        self.text_bank = {}
        self.info_bank = {}
        bankdata = self.storemetod.load_info()
        if bankdata:
            self.info_bank = bankdata

    def add_note(self, note, text):
        self.info_bank[note['id']] = note
        self.text_bank[note['id']] = text

    def get_noteinfo(self, id: str):
        return self.info_bank[id]

    def get_notetext(self, id: str):
        if id not in self.text_bank:
            self.text_bank[id] = self.storemetod.load_text(id)
        return self.text_bank[id]

    def get_notes_by_folder(self, folder_id: str):
        folder_notes = []
        for note in self.info_bank.values():
            if note['folder_id'] == folder_id:
                folder_notes.append(note)
        return folder_notes

    def save_notes(self):
        self.storemetod.save_text(self.text_bank)
        self.storemetod.save_info(self.info_bank)

    def save_tree(self, tree):
        self.storemetod.save_tree(tree)

    def load_tree(self):
        return self.storemetod.load_tree()


class Storage:
    def __init__(self, Name, type):
        self.name = Name
        self.id = uuid.uuid4().hex
        self.type = type
        self.bank = NoteBank(type)
        tree_data = self.bank.load_tree()
        if tree_data:
            self.root_folder = TreeImporter().import_(tree_data)
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
        knots.add_entered_folder(parent_folder, txt_item.text)
        knots.remove_textinput(self)

    def rename_folder(self, txt_item, folder_id):
        self.associated_treenode.text = self.txtinp.text
        knots.rename_entered_folder(txt_item.text, folder_id)
        knots.remove_textinput(self)


class KnotsApp(App):
    title = "Notes"
    atlas_path = 'atlas://images/default/default'
    #   atlas = Atlas('images/default/default.atlas')
    window = Window

    def __init__(self):
        super().__init__()
#        default_storage = Storage("MyStorage", "text")
        self.storages = []
        self.storages.append(Storage("MyStorage", "filesystem"))
        self.storages.append(Storage("MyShelf", "shelf"))
        self.bank = self.storages[0].bank
        self.current = NoteInfo()
        self.current_folder_id = '0'

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

    def init_notes_widgets(self):
        self.root.ids.title.text = self.current.note['title']
        self.root.ids.code.text = self.current.text
        self.root.ids.tags.values = self.current.note['tags']
        self.root.ids.tags.text = "tags"
        self.root.ids.bookmark.disabled = False
        self.root.ids.trash.disabled = False
        if self.current.get_bookmark():
            self.root.ids.bookmark.state = 'down'
        else:
            self.root.ids.bookmark.state = 'normal'
        if self.current.get_trash():
            self.root.ids.trash.state = 'down'
        else:
            self.root.ids.trash.state = 'normal'

    def button_selection(self, instance, pos):
        if pos == 'normal' and \
           str(instance.id) == str(self.current.get_id()):  # TODO: fix broken: crash on click
            self.bank.add_note(self.current.note, self.current.text)
            self.current.new()

        if pos == 'down':
            self.current.button = instance
            self.current.note = self.bank.get_noteinfo(instance.id)
            self.current.text = self.bank.get_notetext(instance.id)

        self.init_notes_widgets()

    def create_new_note(self):
        self.current.note['folder_id'] = self.current_folder_id
        self.add_note_on_bar(self.current.get_id(), "", True)
        for child in self.root.ids.note_bar.children:
            if str(child.id) == str(self.current.get_id()):
                self.current.set_button(child)

        self.root.ids.tags.values = self.current.note['tags']
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
            if self.root.ids.title.text == "" and not self.current.button:
                self.create_new_note()
        else:
            # Remove if empty
            if self.current.button and not self.root.ids.title.text:
                self.root.ids.note_bar.remove_widget(self.current.button)
                self.current.new()

    def kv_bookmarked(self):
        self.current.bookmarked()

    def kv_trashed(self):
        self.current.trashed()

    def kv_tag_added(self, text):
        self.current.add_tag(str(text))
        self.root.ids.tags.values = self.current.note['tags']

    def kv_title_entered(self):
        if self.root.ids.title.text:
            self.current.note['title'] = self.root.ids.title.text
            self.current.button.text = self.root.ids.title.text
            self.current.update_time()

    def kv_code_entered(self):
        self.current.text = self.root.ids.code.text
        self.current.update_time()

    def kv_search_entered(self):
        for butt in self.root.ids.note_bar.children:
            if self.root.ids.search.text not in butt.text:
                butt.opacity = 0.2
                butt.disable = True
            else:
                butt.opacity = 1
                butt.disable = False

    def kv_tree_selected(self, treenode_id):
        if self.current.button:
            self.bank.add_note(self.current.note, self.current.text)
        self.current.new()
        self.init_notes_widgets()
        self.current_folder_id = str(treenode_id)
        self.root.ids.note_bar.clear_widgets()  # clear note_bar
        for note in self.bank.get_notes_by_folder(self.current_folder_id):  # fill note_bar
            self.add_note_on_bar(note['id'], note['title'], False)

    def kv_button_add_folder(self, treenode):
        self.root.ids.folders_tree.add_node(TreeView_NewFolderInput("New folder"), parent=treenode)

    def kv_button_rename_folder(self, treenode):
        self.root.ids.folders_tree.add_node(TreeView_NewFolderInput(treenode.text, treenode=treenode, rename=True))

    def kv_button_test(self):
        pass

    def on_stop(self):
        if self.current.button:
            self.bank.add_note(self.current.note, self.current.text)

        self.bank.save_notes()
        for stor in self.storages:
            if stor.name == "MyStorage":
                exp = TreeExporter(indent=2, sort_keys=True)
                self.bank.save_tree(exp.export(stor.root_folder))

# TODO:  1. Auto save by idle time


if __name__ == "__main__":
    knots = KnotsApp()
    knots.run()
