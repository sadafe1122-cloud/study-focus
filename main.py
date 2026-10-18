"""Study Focus - black OLED study timer (Kivy). Default language: English, Persian supported.
Optional files: assets/Vazirmatn-Regular.ttf (Persian font). pip: arabic-reshaper python-bidi plyer
"""
import json, math, os, random, struct, time, wave
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import platform

Window.clearcolor = (0, 0, 0, 1)
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "assets", "Vazirmatn-Regular.ttf")
DIM = (0.35, 0.35, 0.35, 1)
RING_SECONDS = 180

S = {"lang": "en", "show_clock": True, "show_timer": True, "reveal": 20,
     "minutes": 3, "blackout": False, "sound": "", "clock_reveal": 0, "notify": False,
     "rotation": 0}

T = {
    "en": {"study": "Study", "settings": "Settings", "about": "About", "back": "Back",
           "show_clock": "Show clock", "show_timer": "Show timer",
           "reveal": "Show timer when this close to the alarm", "never": "Never",
           "minutes": "Timer (minutes)", "blackout": "Blackout (hide everything)",
           "sound": "Alarm sound", "default": "Default", "language": "Language",
           "choose": "Choose", "cancel": "Cancel",
           "h_exit": "Hold 3 sec anywhere to exit", "h_stop": "Double-tap to stop timer",
           "h_restart": "Tap here to restart timer", "custom": "Custom",
           "custom_title": "Timer length (minutes)", "ok": "OK", "advanced": "Advanced settings",
           "notify": "Notification when timer is stopped",
           "clock_reveal": "Show clock when this close to the alarm",
           "rotation": "Rotation lock", "auto": "Auto", "portrait": "Portrait", "landscape": "Landscape",
           "n_title": "Timer stopped", "n_text": "Your study timer was stopped."},
    "fa": {"study": "مطالعه", "settings": "تنظیمات", "about": "درباره", "back": "بازگشت",
           "show_clock": "نمایش ساعت", "show_timer": "نمایش زمان‌سنج",
           "reveal": "نمایش زمان‌سنج در چند ثانیهٔ آخر", "never": "هرگز",
           "minutes": "زمان‌سنج (دقیقه)", "blackout": "حالت خاموش (پنهان‌کردن همه‌چیز)",
           "sound": "صدای زنگ", "default": "پیش‌فرض", "language": "زبان",
           "choose": "انتخاب", "cancel": "انصراف",
           "h_exit": "برای خروج، ۳ ثانیه هر جا را نگه دارید", "h_stop": "برای توقف، دو بار لمس کنید",
           "h_restart": "برای شروع دوباره، اینجا را لمس کنید", "custom": "دلخواه",
           "custom_title": "مدت زمان‌سنج (دقیقه)", "ok": "تأیید", "advanced": "تنظیمات پیشرفته",
           "notify": "اعلان هنگام توقف زمان‌سنج",
           "clock_reveal": "نمایش ساعت در چند ثانیهٔ آخر",
           "rotation": "قفل چرخش", "auto": "خودکار", "portrait": "عمودی", "landscape": "افقی",
           "n_title": "زمان‌سنج متوقف شد", "n_text": "زمان‌سنج مطالعه متوقف شد."},
}

ABOUT = ("Developer: Erfan R\nContact: dev.geospatial@gmail.com\n\n"
         "IMPORTANT - OLED ONLY\n"
         "This app is made only for phones with OLED / AMOLED displays. Do not use it on LCD, IPS "
         "or any other non-OLED phone.\n\n"
         "Protect your screen\n"
         "To avoid burn-in, turn off everything that stays fixed on the screen while Study mode is "
         "running: the Assistant menu (Settings > Accessibility > Interaction and dexterity), floating "
         "buttons or bubbles, the edge-panel handle, on-screen navigation buttons and any other overlay. "
         "The clock and timer shift slightly every minute and the text is dim, but this does not remove "
         "the risk completely. Use low brightness.\n\n"
         "Legal notice\n"
         "This app is provided \"as is\", without warranty of any kind. The developer is not liable for "
         "any loss, damage (including screen burn-in or image retention), missed alarm, battery issue or "
         "other consequence arising from its use. Do not rely on it for time-critical or safety-critical "
         "purposes. By using this app you agree to these terms.")


def tr(k):
    return fix(T[S["lang"]][k])


def fix(s):
    if S["lang"] != "fa":
        return s
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return "\n".join(get_display(arabic_reshaper.reshape(x)) for x in s.split("\n"))
    except Exception:
        return s


def fn():
    return FONT if S["lang"] == "fa" and os.path.exists(FONT) else "Roboto"


def lbl(text, **kw):
    kw.setdefault("halign", "right" if S["lang"] == "fa" else "left")
    kw.setdefault("valign", "middle")
    l = Label(text=text, font_name=fn(), **kw)
    l.bind(size=lambda i, s: setattr(i, "text_size", s))
    return l


def btn(text, cb, **kw):
    kw.setdefault("background_color", (0.12, 0.12, 0.12, 1))
    b = Button(text=text, font_name=fn(), background_normal="", **kw)
    b.bind(on_release=lambda *_: cb())
    return b


# ---- Android helpers (silently ignored on Pydroid/desktop) ----
def android_window(action):
    if platform != "android":
        return
    try:
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        @run_on_ui_thread
        def run():
            w = autoclass("org.kivy.android.PythonActivity").mActivity.getWindow()
            action(w)
        run()
    except Exception as e:
        print("android_window:", e)


def set_immersive(on):
    def a(w):
        if on:
            w.addFlags(128)  # KEEP_SCREEN_ON
            w.getDecorView().setSystemUiVisibility(4 | 2 | 4096)
        else:
            w.clearFlags(128)
            w.getDecorView().setSystemUiVisibility(0)
    android_window(a)


def set_brightness(v):
    def a(w):
        lp = w.getAttributes()
        lp.screenBrightness = v
        w.setAttributes(lp)
    android_window(a)


def set_orientation(mode):  # 0 auto, 1 portrait, 2 landscape
    if platform != "android":
        return
    try:
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        @run_on_ui_thread
        def run():
            autoclass("org.kivy.android.PythonActivity").mActivity.setRequestedOrientation([-1, 7, 6][mode])
        run()
    except Exception as e:
        print("orientation:", e)


def make_beep(path):
    if os.path.exists(path):
        return
    sr = 22050
    with wave.open(path, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        for i in range(sr):
            on = (i % (sr // 2)) < sr // 5
            v = int(12000 * math.sin(2 * math.pi * 880 * i / sr)) if on else 0
            f.writeframes(struct.pack("<h", v))


# ---- Screens ----
class Circle(Widget):
    def __init__(self, text, cb, **kw):
        super().__init__(**kw)
        self.cb = cb
        with self.canvas:
            Color(0.8, 0.8, 0.8, 1)
            self.ring = Line(ellipse=(0, 0, 0, 0), width=3)
        self.l = Label(text=text, font_name=fn(), font_size="30sp", color=(0.8, 0.8, 0.8, 1))
        self.add_widget(self.l)
        self.bind(pos=self.upd, size=self.upd)

    def upd(self, *_):
        d = min(self.width, self.height)
        self.ring.ellipse = (self.center_x - d / 2, self.center_y - d / 2, d, d)
        self.l.center = self.center

    def on_touch_down(self, t):
        if self.collide_point(*t.pos):
            self.cb()
            return True


class Menu(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        fl = FloatLayout()
        fl.add_widget(Circle(tr("study"), app.enter_study, size_hint=(0.8, 0.5),
                             pos_hint={"center_x": 0.5, "center_y": 0.5}))
        fl.add_widget(btn(tr("settings"), lambda: setattr(app.sm, "current", "settings"),
                          size_hint=(0.35, 0.07), pos_hint={"right": 0.98, "top": 0.98}))
        self.add_widget(fl)


class Study(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app, self.hold_ev, self.held, self.dbl = app, None, False, False
        self.hints, self.last_m = [], -1
        with self.canvas:
            self.lc = Color(0.35, 0.35, 0.35, 1)
            self.line = Line(points=[], width=1.5)
        self.bind(size=self.draw_line)
        self.box = BoxLayout(orientation="vertical", size_hint=(1, 0.5),
                             pos_hint={"center_x": 0.5, "center_y": 0.5})
        self.clock_l = Label(font_size="64sp", color=DIM)
        self.timer_l = Label(font_size="64sp", color=DIM)
        self.box.add_widget(self.clock_l); self.box.add_widget(self.timer_l)
        self.add_widget(self.box)

    def landscape(self):
        return Window.width > Window.height

    def draw_line(self, *_):
        w, h = Window.size
        self.line.points = [w / 2, 0, w / 2, h] if self.landscape() else [0, h / 2, w, h / 2]

    def start_preview(self):
        self.draw_line()
        self.lc.a = 1
        Clock.schedule_once(lambda dt: Animation(a=0, d=1).start(self.lc), 6)
        land = self.landscape()
        top, bot = ((0.25, 0.5), (0.75, 0.5)) if land else ((0.5, 0.75), (0.5, 0.25))
        for key, (x, y) in (("h_stop", top), ("h_restart", bot), ("h_exit", (0.5, 0.07))):
            l = Label(text=tr(key), font_name=fn(), halign="center", valign="middle", color=DIM,
                      font_size="18sp", size_hint=(0.4 if land else 0.8, 0.2),
                      pos_hint={"center_x": x, "center_y": y})
            l.bind(size=lambda i, sz: setattr(i, "text_size", sz))
            self.hints.append(l)
            self.add_widget(l)
        Clock.schedule_once(self.hide_hint, 6)

    def hide_hint(self, dt):
        for l in self.hints:
            self.remove_widget(l)
        self.hints = []

    def refresh(self, r):
        m = int(time.time() // 60)
        if m != self.last_m:  # anti burn-in: move clock/timer a little every minute
            self.last_m = m
            self.box.pos_hint = {"center_x": 0.5 + random.uniform(-0.04, 0.04),
                                 "center_y": 0.5 + random.uniform(-0.03, 0.03)}
        dark = S["blackout"]
        armed = self.app.end is not None
        show_c = not dark and (S["show_clock"] or (S["clock_reveal"] > 0 and armed and r <= S["clock_reveal"]))
        self.clock_l.opacity = 1 if show_c else 0
        reveal = S["reveal"] > 0 and self.app.end is not None and r <= S["reveal"]
        show_t = not dark and (S["show_timer"] or reveal)
        self.timer_l.opacity = 1 if show_t else 0
        if self.clock_l.opacity:
            self.clock_l.text = time.strftime("%H:%M")
        if show_t:
            s = int(math.ceil(r))
            self.timer_l.text = "%02d:%02d" % (s // 60, s % 60)

    def in_top(self, t):
        return t.x < Window.width / 2 if self.landscape() else t.y > Window.height / 2

    def on_touch_down(self, t):
        self.held, self.dbl = False, t.is_double_tap
        self.hold_ev = Clock.schedule_once(self.long_hold, 3)
        return True

    def long_hold(self, dt):
        self.held = True
        self.app.exit_study()

    def on_touch_up(self, t):
        if self.hold_ev:
            self.hold_ev.cancel()
        if self.held:
            return True
        if self.in_top(t):
            if self.dbl:
                self.app.stop_timer(True)
        else:
            self.app.restart()
        return True


class Page(Screen):
    def __init__(self, app, title, **kw):
        super().__init__(**kw)
        self.app = app
        col = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(6))
        col.add_widget(lbl(title, size_hint_y=None, height=dp(48), font_size="22sp"))
        sv = ScrollView()
        self.g = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        self.g.bind(minimum_height=self.g.setter("height"))
        sv.add_widget(self.g)
        col.add_widget(sv)
        self.bar = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        col.add_widget(self.bar)
        self.add_widget(col)

    def row(self, key, w):
        r = BoxLayout(size_hint_y=None, height=dp(56))
        r.add_widget(lbl(tr(key)))
        r.add_widget(w)
        self.g.add_widget(r)

    def sw(self, key):
        s = Switch(active=S[key], size_hint_x=0.4)
        s.bind(active=lambda i, v: self.app.setting(key, v))
        return s

    def reveal(self, key):
        vals = ["10 s", "20 s", "30 s", tr("never")]
        nums = [10, 20, 30, 0]
        sp = Spinner(text=vals[nums.index(S[key])], values=vals, font_name=fn(), size_hint_x=0.4)
        sp.bind(text=lambda i, v: self.app.setting(key, nums[vals.index(v)]))
        self.row(key, sp)


class Settings(Page):
    def __init__(self, app, **kw):
        super().__init__(app, tr("settings"), **kw)
        self.row("show_clock", self.sw("show_clock"))
        self.row("show_timer", self.sw("show_timer"))
        self.reveal("reveal")
        self.minutes_row()
        self.row("blackout", self.sw("blackout"))
        rot = [tr("auto"), tr("portrait"), tr("landscape")]
        sp = Spinner(text=rot[S["rotation"]], values=rot, font_name=fn(), size_hint_x=0.4)
        sp.bind(text=lambda i, v: app.set_rotation(rot.index(v)))
        self.row("rotation", sp)
        name = os.path.basename(S["sound"]) if S["sound"] else tr("default")
        self.row("sound", btn(name, self.pick_sound, size_hint_x=0.4))
        langs = ["English", "Persian (Farsi)"]
        sp = Spinner(text=langs[S["lang"] == "fa"], values=langs, size_hint_x=0.4)
        sp.bind(text=lambda i, v: app.set_lang("fa" if "Farsi" in v else "en"))
        self.row("language", sp)
        self.g.add_widget(btn(tr("advanced"), lambda: setattr(app.sm, "current", "advanced"),
                              size_hint_y=None, height=dp(52)))
        self.bar.add_widget(btn(tr("about"), self.show_about, background_color=(0, 0, 0, 1), color=DIM))
        self.bar.add_widget(btn(tr("back"), lambda: setattr(app.sm, "current", "menu")))

    def minutes_row(self):
        app = self.app
        holder = BoxLayout(size_hint_x=0.4, spacing=dp(4))
        sp = Spinner(text="%g" % S["minutes"], values=["1.5", "2.5", "3", "5", tr("custom")], font_name=fn())
        holder.add_widget(sp)

        def pick(i, v):
            if v != tr("custom"):
                app.setting("minutes", float(v))
                return
            holder.clear_widgets()
            ti = TextInput(text="%g" % S["minutes"], input_filter="float", multiline=False, font_size="20sp")

            def done(*_):
                try:
                    val = float(ti.text)
                except ValueError:
                    val = 0
                if 0.1 <= val <= 600:
                    app.setting("minutes", val)
                ti.focus = False
                Clock.schedule_once(lambda dt: app.rebuild("settings"), 0.1)
            ti.bind(on_text_validate=done)
            holder.add_widget(ti)
            holder.add_widget(btn(tr("ok"), done, size_hint_x=0.4))
            Clock.schedule_once(lambda dt: setattr(ti, "focus", True), 0.1)
        sp.bind(text=pick)
        self.row("minutes", holder)

    def show_about(self):
        sv = ScrollView()
        l = Label(text=ABOUT, halign="left", valign="top", size_hint_y=None)
        l.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
        l.bind(texture_size=lambda i, s: setattr(i, "height", s[1]))
        sv.add_widget(l)
        Popup(title="About", content=sv, size_hint=(0.92, 0.8)).open()

    def pick_sound(self):
        start = "/storage/emulated/0" if os.path.isdir("/storage/emulated/0") else HERE
        fc = FileChooserListView(path=start, filters=["*.mp3", "*.wav", "*.ogg"])
        box = BoxLayout(orientation="vertical")
        box.add_widget(fc)
        bar = BoxLayout(size_hint_y=None, height=dp(48))
        pop = Popup(title=tr("sound"), title_font=fn(), content=box, size_hint=(0.95, 0.9))

        def ok():
            if fc.selection:
                self.app.setting("sound", fc.selection[0])
                Clock.schedule_once(lambda dt: self.app.rebuild("settings"), 0)
            pop.dismiss()
        bar.add_widget(btn(tr("choose"), ok))
        bar.add_widget(btn(tr("cancel"), pop.dismiss))
        box.add_widget(bar)
        pop.open()


class Advanced(Page):
    def __init__(self, app, **kw):
        super().__init__(app, tr("advanced"), **kw)
        self.row("notify", self.sw("notify"))
        self.reveal("clock_reveal")
        self.bar.add_widget(btn(tr("back"), lambda: setattr(app.sm, "current", "settings")))


# ---- App ----
class StudyApp(App):
    def build(self):
        self.cfg = os.path.join(self.user_data_dir, "settings.json")
        try:
            S.update(json.load(open(self.cfg)))
        except Exception:
            pass
        self.beep = os.path.join(self.user_data_dir, "beep.wav")
        make_beep(self.beep)
        self.end, self.ringing, self.sound, self.ring_ev, self.tick_ev = None, False, None, None, None
        Window.softinput_mode = "below_target"
        set_immersive(False)
        set_brightness(-1.0)
        set_orientation(S["rotation"])
        if platform == "android":
            try:
                from android.permissions import request_permissions
                request_permissions(["android.permission.POST_NOTIFICATIONS"])
            except Exception as e:
                print(e)
        Window.bind(on_keyboard=self.on_key)
        self.root_box = BoxLayout()
        self.rebuild()
        return self.root_box

    def rebuild(self, current="menu"):
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(Menu(self, name="menu"))
        self.sm.add_widget(Settings(self, name="settings"))
        self.sm.add_widget(Advanced(self, name="advanced"))
        self.sm.add_widget(Study(self, name="study"))
        self.sm.current = current
        self.root_box.clear_widgets(); self.root_box.add_widget(self.sm)

    def setting(self, k, v):
        S[k] = v
        try:
            json.dump(S, open(self.cfg, "w"))
        except Exception as e:
            print(e)

    def set_lang(self, lang):
        if lang != S["lang"]:
            self.setting("lang", lang)
            Clock.schedule_once(lambda dt: self.rebuild("settings"), 0)

    def set_rotation(self, mode):
        self.setting("rotation", mode)
        set_orientation(mode)

    def on_pause(self):
        return True

    def on_resume(self):
        if self.sm.current == "study":
            set_immersive(True)

    def on_stop(self):
        set_immersive(False)
        set_brightness(-1.0)

    def on_key(self, win, key, *a):
        if key != 27:
            return False
        if self.sm.current == "study":
            self.exit_study()
        elif self.sm.current != "menu":
            self.sm.current = "menu"
        else:
            return False
        return True

    # study mode
    def enter_study(self):
        self.sm.current = "study"
        set_immersive(True)
        if S["blackout"]:
            set_brightness(0.0)
        self.restart()
        self.sm.get_screen("study").start_preview()
        self.tick_ev = Clock.schedule_interval(self.tick, 1)
        self.tick(0)

    def exit_study(self):
        if self.tick_ev:
            self.tick_ev.cancel()
        self.stop_timer(False)
        set_immersive(False); set_brightness(-1.0)
        self.sm.current = "menu"

    # timer
    def remaining(self):
        return S["minutes"] * 60 if self.end is None else max(0, self.end - time.monotonic())

    def tick(self, dt):
        r = self.remaining()
        if self.end is not None and r <= 0 and not self.ringing:
            self.ring()
        self.sm.get_screen("study").refresh(r)

    def restart(self):
        self.stop_ring()
        self.end = time.monotonic() + S["minutes"] * 60

    def stop_timer(self, notify):
        self.stop_ring()
        self.end = None
        if notify and S["notify"]:
            try:
                from plyer import notification
                notification.notify(title=T[S["lang"]]["n_title"], message=T[S["lang"]]["n_text"], timeout=5)
            except Exception as e:
                print("notify:", e)
        if self.sm.current == "study":
            self.sm.get_screen("study").refresh(self.remaining())

    def ring(self):
        self.ringing = True
        self.sound = SoundLoader.load(S["sound"] if S["sound"] and os.path.exists(S["sound"]) else self.beep)
        if self.sound:
            self.sound.loop = True
            self.sound.play()
        self.ring_ev = Clock.schedule_once(self.ring_timeout, RING_SECONDS)

    def ring_timeout(self, dt):
        self.stop_ring()
        self.end = None

    def stop_ring(self):
        if self.ring_ev:
            self.ring_ev.cancel(); self.ring_ev = None
        if self.sound:
            self.sound.stop(); self.sound = None
        self.ringing = False


if __name__ == "__main__":
    StudyApp().run()
