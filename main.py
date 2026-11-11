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

    def __init__(self, **kw):
        super().__init__(**kw)
        self._sx = 0
        self._sy = 0
        self._long_event = None

    def get_scroll(self):
        return self.ids.scroll.scroll_y

    def set_scroll(self, y):
        self.ids.scroll.scroll_y = y

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            self._sx = touch.x
            self._sy = touch.y
            if getattr(app, "last_ref", None):
                self._long_event = Clock.schedule_once(
                    lambda dt: app.show_long_ref(), 0.7
                )
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        res = super().on_touch_up(touch)
        if self._long_event is not None:
            self._long_event.cancel()
            self._long_event = None
        if not self.collide_point(touch.x, touch.y):
            return res
        dx = touch.x - self._sx
        dy = touch.y - self._sy
        w = self.width
        if abs(dx) > w * 0.2 and abs(dx) > abs(dy):
            if dx < 0:
                app.next_chapter()
            else:
                app.prev_chapter()
        elif abs(dy) < 10:
            if touch.x > w * 0.85:
                app.next_chapter()
            elif touch.x < w * 0.15:
                app.prev_chapter()
        return res


class MainApp(MDApp):
    current = 0
    bookmark = None
    last_ref = None

    def build(self):
        self.pos_cache = {}
        self.load_data()
        Builder.load_string(KV)
        self.sm = MDScreenManager()
        self.home = MDScreen(name="home")
        self.home.add_widget(MDTopAppBar(
            title="Оглавление", pos_hint={"top": 1}))
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
        if idx < 0 or idx >= len(self.chapters):
            return
        self.current = idx
        ch = self.chapters[idx]
        text = "\n\n".join(
            "[b]" + s["title"] + "[/b]\n" + s["text"]
            for s in ch["sections"]
        )
        text = text.replace("[ref:", "[ref=")
        key = "scr_" + ch["id"]
        for s in list(self.sm.screens):
            if s.name == key:
                self.sm.remove_widget(s)
        scr = ChapterScreen(name=key, title=ch["title"], text=text)
        self.sm.add_widget(scr)
        self.sm.current = key
        Clock.schedule_once(lambda dt: self.restore(scr), 0.3)

    def next_chapter(self):
        self.open_chapter(self.current + 1)

    def prev_chapter(self):
        self.open_chapter(self.current - 1)

    def go_home(self):
        self.save_progress()
        self.sm.current = "home"

    def restore(self, scr):
        cid = self.chapters[self.current]["id"]
        scr.set_scroll(self.pos_cache.get(cid, 0))

    def save_progress(self):
        if not isinstance(self.sm.current_screen, ChapterScreen):
            return
        cid = self.chapters[self.current]["id"]
        self.pos_cache[cid] = self.sm.current_screen.get_scroll()
        try:
            with open("progress.json", "w") as f:
                json.dump(
                    {"chapter": self.current, "cache": self.pos_cache}, f
                )
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
        self.last_ref = ref
        data = self.glossary.get(ref, {})
        self.show_dialog(
            "Определение",
            data.get("short", "Нет описания"),
            data.get("long", ""),
        )

    def show_long_ref(self):
        ref = self.last_ref
        if not ref:
            return
        data = self.glossary.get(ref, {})
        self.show_dialog(
            "Подробно",
            data.get("long", "Нет описания"),
            "",
        )

    def show_dialog(self, title, short, long):
        txt = short
        if long:
            txt += "\n\n" + long
        buttons = [MDFlatButton(
            text="OK",
            on_release=lambda x: self.dlg.dismiss(),
        )]
        self.dlg = MDDialog(
            title=title, text=txt, buttons=buttons,
            size_hint=(0.9, None),
        )
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
            Clock.schedule_once(
                lambda dt: self.sm.current_screen.set_scroll(y), 0.3
            )

    def on_stop(self):
        self.save_progress()


if __name__ == "__main__":
    MainApp().run()