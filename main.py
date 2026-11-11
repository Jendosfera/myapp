import json, os
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.toolbar import MDTopAppBar

KV = '''
<ChapterScreen>:
    MDTopAppBar:
        title: root.title
        pos_hint: {"top": 1}
        left_action_items: [["arrow-left", lambda x: app.go_home()]]
        right_action_items: [["bookmark-outline", lambda x: app.on_bookmark_button()], ["home", lambda x: app.go_home()]]
    ScrollView:
        id: scroll
        MDLabel:
            id: lbl
            text: root.text
            markup: True
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width - dp(20), None
            padding: dp(10), dp(10)
            on_ref_press: app.on_ref_press(args[1])
'''

class ChapterScreen(MDScreen):
    title = StringProperty("")
    text = StringProperty("")
    def get_scroll(self):
        return self.ids.scroll.scroll_y
    def set_scroll(self, y):
        self.ids.scroll.scroll_y = y

class MainApp(MDApp):
    current = 0
    bookmark = None
    def build(self):
        self.load_data()
        Builder.load_string(KV)
        self.sm = MDScreenManager()
        self.home = MDScreen(name="home")
        self.home.add_widget(MDTopAppBar(title="Оглавление", pos_hint={"top": 1}))
        self.lst = MDList()
        self.home.add_widget(self.lst)
        self.sm.add_widget(self.home)
        self.build_list()
        self.load_progress()
        return self.sm
    def load_data(self):
        with open("content.json", encoding="utf-8") as f:
            self.chapters = json.load(f)["chapters"]
        with open("glossary.json", encoding="utf-8") as f:
            self.glossary = json.load(f)
    def build_list(self):
        self.lst.clear_widgets()
        for i, ch in enumerate(self.chapters):
            it = OneLineListItem(text=ch["title"])
            it.bind(on_release=lambda x, k=i: self.open_chapter(k))
            self.lst.add_widget(it)
    def open_chapter(self, idx):
        self.current = idx
        ch = self.chapters[idx]
        text = "\n\n".join("[b]" + s["title"] + "[/b]\n" + s["text"] for s in ch["sections"])
        key = "scr_" + ch["id"]
        scr = ChapterScreen(name=key, title=ch["title"], text=text)
        self.sm.add_widget(scr)
        self.sm.current = key
        Clock.schedule_once(lambda dt: self.restore(scr), 0.3)
    def go_home(self):
        self.save_progress()
        self.sm.current = "home"
    def restore(self, scr):
        scr.set_scroll(self.pos_cache.get(self.chapters[self.current]["id"], 0))
    def save_progress(self):
        if not isinstance(self.sm.current_screen, ChapterScreen):
            return
        cid = self.chapters[self.current]["id"]
        self.pos_cache[cid] = self.sm.current_screen.get_scroll()
        try:
            with open("progress.json", "w") as f:
                json.dump({"chapter": self.current, "cache": self.pos_cache}, f)
        except Exception:
            pass
    def load_progress(self):
        self.pos_cache = {}
        if os.path.exists("progress.json"):
            try:
                with open("progress.json") as f:
                    p = json.load(f)
                    self.current = p.get("chapter", 0)
                    self.pos_cache = p.get("cache", {})
            except Exception:
                pass
    def on_ref_press(self, ref):
        data = self.glossary.get(ref, {})
        self.show_dialog("Определение", data.get("short", "Нет описания"), data.get("long", ""))
    def show_dialog(self, title, short, long):
        txt = short + ("\n\n" + long if long else "")
        self.dlg = MDDialog(title=title, text=txt, size_hint=(0.9, None),
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dlg.dismiss())])
        self.dlg.open()
    def on_bookmark_button(self):
        scr = self.sm.current_screen
        if not isinstance(scr, ChapterScreen):
            return
        if self.bookmark is None:
            self.bookmark = (self.current, scr.get_scroll())
            self.show_dialog("Закладка", "Место сохранено", "")
        else:
            idx, y = self.bookmark
            self.open_chapter(idx)
            Clock.schedule_once(lambda dt: self.sm.current_screen.set_scroll(y), 0.3)
    def on_stop(self):
        self.save_progress()

MainApp().run()