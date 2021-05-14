import time, uuid, anytree
import re
import json
from anytree.importer import JsonImporter as TreeImporter
from anytree.exporter import JsonExporter as TreeExporter
from inspect import getmembers as gm
from pprint import pprint as pp
from functools import partial
from kivy.app import App
from kivy.config import Config
from kivy.properties import StringProperty, DictProperty, ObjectProperty, ListProperty
from kivy.atlas import Atlas
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton as button, Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.accordion import Accordion, AccordionItem, AccordionException
from kivy.uix.settings import SettingsWithSidebar, SettingItem, SettingPath  # SettingsWithTabbedPanel
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.animation import Animation
from kivy.weakproxy import WeakProxy
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.properties import ConfigParser, ConfigParserProperty
from pygments import lexers
import knot_modules
# import shaders

Config.set('input', 'mouse', 'mouse, multitouch_on_demand')
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'log_level', 'warning')  # string, one of ‘trace’, ‘debug’, ‘info’, ‘warning’, ‘error’ or ‘critical’
Config.write()


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

    def get_all_tags(self):
        all_tags = set()
        for note_tags in [note['tags'] for note in self.info_bank.values() if note['tags']]:
            [all_tags.add(tag) for tag in note_tags]
        return all_tags

    def get_all_codes(self):
        return [note['codetype'] for note in self.info_bank.values() if note['codetype']]

    def get_notes_by_folder(self, folder_id: str):
        return [note for note in self.info_bank.values() if note['folder_id'] == folder_id]

    def get_notes_by_tag(self, tag):
        return [note for note in self.info_bank.values() if tag in note['tags']]

    def get_notes_by_codetype(self, codetype):
        return [note for note in self.info_bank.values() if note['codetype'] == codetype]

    def get_notes_by_bookmark(self):
        return [note for note in self.info_bank.values() if note['bookmark']]

    def get_notes_by_trashcan(self):
        return [note for note in self.info_bank.values() if note['trash']]

    def save_notes(self):
        self.storemetod.save_text(self.text_bank)
        self.storemetod.save_info(self.info_bank)

    def save_tree(self, tree):
        self.storemetod.save_tree(tree)

    def load_tree(self):
        return self.storemetod.load_tree()

    def search(self, phrase, regex):
        total_keys = self.search_bank(phrase, regex)
        store_keys = self.search_store(phrase, regex)

        # Check store_keys id is real and not in memory cache
        for sk in store_keys:
            if sk in self.info_bank.keys() and sk not in self.text_bank.keys():
                total_keys.append(sk)

        return total_keys

    def search_store(self, phrase, regex):
        return self.storemetod.search(phrase, regex)

    def search_method(self, phrase, str_line, regex):
        if regex:
            return bool(re.match(phrase, str_line))
        else:
            return phrase in str(str_line)

    def search_bank(self, phrase, regex):
        found_phrases_id = []
        for key, text in self.text_bank.items():
            if self.search_method(phrase, text, regex):
                found_phrases_id.append(key)
        return found_phrases_id

class Storage:
    def __init__(self, Name, type):
        self.name = Name
        self.id = uuid.uuid4().hex
        self.type = type
        self.bank = NoteBank(type)
        self.tree_view = None
        tree_data = self.bank.load_tree()
        if tree_data:
            self.root_folder = TreeImporter().import_(tree_data)
        else:
            self.root_folder = ThemeFolders(self.name)


class StorageSelector(Accordion):
    orientation = 'vertical'
    selected = DictProperty()

    def __init__(self, **kwargs):
        super(StorageSelector, self).__init__(**kwargs)

    def select(self, instance):
        self.selected = {"id": instance.id, "title": instance.title}
        if instance not in self.children:
            raise AccordionException('Accordion: instance not found in children')
        for widget in self.children:
            widget.collapse = widget is not instance
        self._trigger_layout()


class ThemeFolders(anytree.NodeMixin):  # Add Node feature
    def __init__(self, name, parent=None, children=None):
        self.name = name
        self.id = str(uuid.uuid4())
        self.parent = parent
        if children:
            self.children = children


class TreeViewIDLabel(TreeViewLabel):
    def __init__(self, label_id: str = None, **kwargs):
        self.label_id = label_id
        super(TreeViewIDLabel, self).__init__(**kwargs)


class TreeView_NewFolderInput(BoxLayout, TreeViewNode):
    def __init__(self, msg: str, treenode: TreeViewLabel = None, rename: bool = False, **kwargs):
        super(TreeView_NewFolderInput, self).__init__(**kwargs)
        self.associated_treenode = treenode
        self.height = 32
        self.txtinp = TextInput(text=msg, multiline=False)
        if not rename:
            self.txtinp.bind(on_text_validate=self.add_new_folder)
            self.txtinp.bind(on_focus=self.add_new_folder)
        else:
            self.txtinp.bind(on_text_validate=partial(self.rename_folder, folder_id=treenode.label_id))
            self.txtinp.bind(on_focus=partial(self.rename_folder, folder_id=treenode.label_id))
        self.add_widget(self.txtinp)

    def add_new_folder(self, txt_item):
        parent_folder = super().parent_node
        knots.add_entered_folder(parent_folder, txt_item.text)
        knots.remove_textinput(self)

    def rename_folder(self, txt_item, folder_id):
        self.associated_treenode.text = self.txtinp.text
        knots.rename_entered_folder(txt_item.text, folder_id)
        knots.remove_textinput(self)


class SettingCodeMenu(SettingItem):
    '''
    (internal) Used to store the current popup when it is shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults to None.
    '''

    #get_codetypes = ConfigParser.get_configparser('app') #

    options = ''
    popup = ObjectProperty(None, allownone=True)

    # def __init__(self):
    #     get_codetypes = ConfigParserProperty('markdown', 'First', 'code_types', 'app', val_type=str)  # ListProperty()
    #     pp(self.app.code_types)
    #     for cde in get_codetypes:
    #         pp(str(cde))

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind('on_release', self._create_popup)

    def _set_option(self, instance):
        self.value = ",".join(self.options)
        self.popup.dismiss()

    def _add_lang(self, btn):
        self.options.append(btn.text)

    def _rm_lang(self, btn):
        self.options.remove(btn.text)

    def _create_popup(self, instance):
        # create the popup
        content = BoxLayout(orientation='vertical', spacing='5dp')
        popup_width = min(0.95 * Window.width, dp(700))
        self.popup = Popup(content=content, title=self.title, size_hint=(None, None), size=(popup_width, '400dp'))
        self.popup.height = 0.95 * Window.height

        # add all the options
        #content.add_widget(Widget(size_hint_y=None, height=1))
        scrolls_box = BoxLayout(orientation='horizontal', spacing='5dp')
        layout_all = GridLayout(cols=1, padding=5, spacing=5, size_hint=(None, None))
        layout_all.bind(minimum_height=layout_all.setter('height'))
        scroll_all = ScrollView(size_hint=(None, None), size=(300, 320), pos_hint={'center_x': .5, 'center_y': .5}, do_scroll_x=False)
        lex_gen = (lex[0] for lex in lexers.get_all_lexers())
        for lex in lex_gen:
            btn = Button(text=str(lex), size=(300, 30), size_hint=(None, None))
            btn.bind(on_release=self._add_lang)
            layout_all.add_widget(btn)
        scroll_all.add_widget(layout_all)
        scrolls_box.add_widget(scroll_all)

        layout_use = GridLayout(cols=1, padding=5, spacing=5, size_hint=(None, None))
        layout_use.bind(minimum_height=layout_use.setter('height'))
        scroll_use = ScrollView(size_hint=(None, None), size=(300, 320), pos_hint={'center_x': .5, 'center_y': .5}, do_scroll_x=False)
        for opt in self.options:
            btn = Button(text=str(opt), size=(300, 30), size_hint=(None, None))
            btn.bind(on_release=self._rm_lang)
            layout_use.add_widget(btn)

        scroll_use.add_widget(layout_use)
        scrolls_box.add_widget(scroll_use)
        content.add_widget(scrolls_box)

        btn_ok = Button(text='OK', size_hint_y=None, height=dp(50))
        btn_ok.bind(on_release=self._set_option)

        btn_cl = Button(text='Cancel', size_hint_y=None, height=dp(50))
        btn_cl.bind(on_release=self.popup.dismiss)
        content.add_widget(btn_ok)
        content.add_widget(btn_cl)

        # and open the popup !
        self.popup.open()


settings_json = '''
[
    {
        "type": "codemenu",
        "title": "Used code languages",
        "desc": "Choose the code languages",
        "section": "First",
        "key": "code_types"
    }
]
'''


class KnotsApp(App):
    title = "Knots"
    atlas_path = 'atlas://images/default/default'
    #   atlas = Atlas('images/default/default.atlas')
    window = Window

    def __init__(self):
        super().__init__()
        self.settings_cls = SettingsWithSidebar
        self.button_style = {"vsize": 56, "valign": "middle", "short": False, "textrows": 2}
        self.storages = []
        self.storages.append(Storage("MyStorage", "filesystem"))
        self.storages.append(Storage("MyShelf", "shelf"))
        self.current = NoteInfo()
        self.current_storage_id = self.storages[0].id
        self.current_tab = "folders"
        self.current_folder_id = '0'
        self.bank = self.storages[0].bank
    #    Clock.schedule_interval(self.bank.save_notes(), 60 * 10)   # Save notes automatically every 10 min

    def build_config(self, config):
        config.setdefaults('First', {'code_types': ['markdown']})

    def build_settings(self, settings):
        self.use_kivy_settings = False
        def_codetypes = self.config.get('First', 'code_types').split(',')
        settings.register_type('codemenu', SettingCodeMenu)
        settings.add_json_panel('Base', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            token = (section, key)
            if token == ('First', 'code_types'):
                self.root.ids.enter_codetype.values = value.split(',')

    def build(self):
        self.root.ids.note_bar.bind(minimum_height=self.root.ids.note_bar.setter('height'))
        self.root.ids.note_bar.row_default_height = self.button_style["vsize"]
        self.root.ids.title.keyboard_on_key_down = self.keyboard_on_key_down
        for each in self.storages:
            self.root.ids.storages.add_widget(self.fill_accordion_item(each))
        self.root.ids.folders_tab.state = 'down'

        #lex_gen = (lex[0] for lex in lexers.get_all_lexers())
        self.root.ids.enter_codetype.values = self.config.get('First', 'code_types').split(',')  # [lex for lex in lex_gen]

    def get_current_storage(self):
        return [st for st in self.storages if st.id == self.current_storage_id][0]

    def fill_accordion_item(self, store):
        storage_butt = AccordionItem()
        storage_butt.id = str(store.id)
        storage_butt.height = 22
        storage_butt.title = str(store.name)

        scroll = ScrollView()
        scroll.do_scroll_x = False
        scroll.size_hint = (1, 1)
        scroll.bar_color = [.5, .10, .15, .8]
        scroll.bar_inactive_color = [.5, .20, .10, .5]
        scroll.scroll_type = ['bars']  # [‘bars’, ‘content’]

        tree_obj = TreeView()
        tree_obj.size_hint = (1, None)
        tree_obj.hide_root = True

        store.tree_view = WeakProxy(tree_obj)
        scroll.add_widget(tree_obj)
        storage_butt.add_widget(scroll)
        return storage_butt

    def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'tab' or keycode[1] == 'enter':
            self.root.ids.code.focus = True
        return True

    def tv_tree_selected(self, tvl, mouse):
        self.clear_notes_and_notebar()

        if self.current_tab == "folders":
            self.current_folder_id = str(tvl.label_id)
            for note in self.bank.get_notes_by_folder(self.current_folder_id):  # fill note_bar
                self.add_note_on_bar(note['id'], note['title'], False)

        if self.current_tab == "tags":
            tag = tvl.text
            for note in self.bank.get_notes_by_tag(tag):
                self.add_note_on_bar(note['id'], note['title'], False)

        if self.current_tab == "codetypes":
            code = tvl.text
            for note in self.bank.get_notes_by_codetype(code):
                self.add_note_on_bar(note['id'], note['title'], False)

    def add_entered_folder(self, parent, folder_name):
        root_folder = self.get_current_storage().root_folder
        parent_folder = anytree.find_by_attr(root_folder, name="id", value=parent.label_id)
        current_folder = ThemeFolders(folder_name, parent=parent_folder)

        self.populate_tree_view(self.get_current_storage().tree_view, parent, current_folder)

    def rename_entered_folder(self, folder_name, folder_id):
        root_folder = self.get_current_storage().root_folder
        current_folder = anytree.find_by_attr(root_folder, name="id", value=folder_id)
        current_folder.name = folder_name

    def remove_textinput(self, treenode):
        self.get_current_storage().tree_view.remove_node(treenode)

    def populate_tree_view(self, tree_view, parent, node):
        tvl = TreeViewIDLabel(label_id=node.id, text=node.name, is_open=True)
        tvl.bind(is_selected=self.tv_tree_selected)
        tree_node = tree_view.add_node(tvl, parent)

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
                str(instance.id) == str(self.current.get_id()):
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
        note_butt.valign = self.button_style["valign"]
        note_butt.max_lines = self.button_style["textrows"]
        note_butt.shorten = self.button_style["short"]
        note_butt.shorten_from = "right"
        note_butt.text_size = (self.root.ids.note_bar.width - 20, self.button_style["vsize"] - 4)  # (180, None)
        if current:
            note_butt.state = 'down'
        note_butt.bind(state=self.button_selection)
        self.root.ids.note_bar.add_widget(note_butt)

    def clear_notes_and_notebar(self):
        if self.current.button:
            self.bank.add_note(self.current.note, self.current.text)
        self.current.new()
        self.init_notes_widgets()
        self.root.ids.note_bar.clear_widgets()  # clear note_bar

    def kv_storage_selected(self, value):
        self.current_storage_id = value.id
        self.bank = self.get_current_storage().bank      # Change bank notes
        self.clear_notes_and_notebar()

        if self.current_tab == "bookmarks":
            for note in self.bank.get_notes_by_bookmark():
                self.add_note_on_bar(note['id'], note['title'], False)

        if self.current_tab == "trash":
            for note in self.bank.get_notes_by_trashcan():
                self.add_note_on_bar(note['id'], note['title'], False)

    def kv_tab_selected(self, tab_type):
        self.current_tab = tab_type

        for storage in self.storages:
            if storage.tree_view:
                for tvl in storage.tree_view.children:
                    storage.tree_view.remove_node(tvl)

                if tab_type == "folders":
                    self.populate_tree_view(storage.tree_view, None, storage.root_folder)

                if tab_type == "tags":
                    for tag in storage.bank.get_all_tags():
                        tvl = TreeViewIDLabel(text=tag)
                        tvl.bind(is_selected=self.tv_tree_selected)
                        storage.tree_view.add_node(tvl)

                if tab_type == "codetypes":
                    for code in storage.bank.get_all_codes():
                        tvl = TreeViewIDLabel(text=code)
                        tvl.bind(is_selected=self.tv_tree_selected)
                        storage.tree_view.add_node(tvl)

    def kv_button_splitter_release(self):
        for butt in self.root.ids.note_bar.children:
            butt.text_size = (self.root.ids.note_bar.width - 20, self.button_style["vsize"] - 4)

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

    def kv_filter_entered(self):
        for butt in self.root.ids.note_bar.children:
            if self.root.ids.search.text not in butt.text:
                butt.height = 0
                #butt.width = 0
                butt.opacity = 1
                butt.size_hint = (None, None)
                butt.disable = True
            else:
                butt.height = self.button_style['vsize']
                butt.opacity = 1
                butt.size_hint_y = 1
                butt.disable = False

    def kv_search_validate(self, text, reg):
        self.clear_notes_and_notebar()
        harvest = self.bank.search(text, regex=reg)
        if harvest:
            for note_id in harvest:
                self.add_note_on_bar(note_id, self.bank.get_noteinfo(note_id)['title'], False)

    def kv_fl_tree_selected(self, treenode_id):
        self.clear_notes_and_notebar()
        self.current_folder_id = str(treenode_id)
        for note in self.bank.get_notes_by_folder(self.current_folder_id):  # fill note_bar
            self.add_note_on_bar(note['id'], note['title'], False)

    def kv_button_add_folder(self):
        tree = self.get_current_storage().tree_view
        if tree.selected_node:
            tree.add_node(TreeView_NewFolderInput("New folder"), parent=tree.selected_node)

    def kv_button_rename_folder(self):
        tree = self.get_current_storage().tree_view
        if tree.selected_node:
            tree.add_node(TreeView_NewFolderInput(tree.selected_node.text, treenode=tree.selected_node, rename=True), parent=tree.selected_node)

    def kv_button_test(self):
        pass

    def on_stop(self):
        if self.current.button:
            self.bank.add_note(self.current.note, self.current.text)

        self.bank.save_notes()

        stor = self.get_current_storage()
        exp = TreeExporter(indent=2, sort_keys=True)
        self.bank.save_tree(exp.export(stor.root_folder))


# TODO:  1. Auto save by idle time


if __name__ == "__main__":
    knots = KnotsApp()
    knots.run()
