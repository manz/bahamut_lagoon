import os
import xml.etree.ElementTree as ET
from array import array

import numpy as np
from kivy.app import App
from kivy.base import EventLoop
from kivy.graphics import *
from kivy.graphics.texture import Texture
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from script import Table

root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

_char_cache = {}


def get_char(data, char):
    char_data = data[char * 17 : (char + 1) * 17 - 1]
    char_width = data[((char + 1) * 17) - 1]
    retval = []
    for b in char_data:
        retval.append([int(k) for k in f"{b:08b}"][:char_width])
    return np.pad(retval, [(0, 0), (0, 1)], mode="constant")


fr_table = Table(os.path.join(root_dir, "text/table/mz.tbl"))

with open(os.path.join(root_dir, "assets/vwf.bin"), "rb") as vwf:
    VWF_DATA = vwf.read()

# Should be loaded from names.xml
NAMES = [
    "Byuu",
    "Yoyo",
    "Salamando",
    "Ice",
    "Thunder",
    "Morten",
    "TwinHead",
    "Munimuni",
    "Papi",
    "Fareneit",
    "Palperos",
    "Matelite",
    "Sendak",
    "Rush",
    "Bikebake",
    "Truth",
    "Taicho",
    "Gunso",
    "Barclay",
    "Donfan",
    "Fils de Zora",
    "Reeve",
    "Frunze",
    "Zeroshin",
    "Sajin",
    "Ruki",
    "Melody",
    "Frederica",
    "Nerbo",
    "Joy",
    "Mist",
    "Jeanne",
    "Diana",
    "Anastasia",
    "Zora",
    "Ekaterina",
    "Wagahai",
    "Monyo",
    "Manyo",
    "Munyo",
]


def expand_char_names(binary_text):
    character_code = fr_table.to_bytes("[character]")[0]

    retval = bytearray()
    k = 0
    while k < len(binary_text):
        char = binary_text[k]
        if char == character_code:
            k += 1
            char_index = binary_text[k]
            retval = retval + fr_table.to_bytes(NAMES[char_index])
        else:
            retval.append(char)
        k += 1
    return retval


def get_array_for_text(text):
    binary_text = fr_table.to_bytes(text.replace(" ", r"\s"))
    binary_text = expand_char_names(binary_text)
    binary_new_line = fr_table.to_bytes("\n")[0]
    buffer = np.zeros((BUFFER_HEIGHT, BUFFER_WIDTH))
    x = 0
    y = 0
    for k in range(len(binary_text)):
        char = binary_text[k]
        if char == binary_new_line:
            x = 0
            y += 16
        else:
            char_buffer = get_char(VWF_DATA, char)
            if x + char_buffer.shape[1] > BUFFER_WIDTH:
                delta = x + char_buffer.shape[1] - BUFFER_WIDTH - 2
                # HACK: it *kinda* work
                left_part = char_buffer[0:, :delta]
                right_part = char_buffer[0:, delta:]

                buffer[y : y + left_part.shape[0], x : x + left_part.shape[1]] = left_part
                x = 0
                y += 16
                buffer[y : y + right_part.shape[0], x : x + right_part.shape[1]] = right_part
                x = right_part.shape[1]

            else:
                buffer[y : y + char_buffer.shape[0], x : x + char_buffer.shape[1]] = char_buffer
                x += char_buffer.shape[1]

            if x == BUFFER_WIDTH:
                y += 16
                x = 0
    return np.uint8(buffer * 255)


WINDOW_COUNT = 8
BUFFER_WIDTH = 256 - 16
BUFFER_HEIGHT = 16 * 3 * WINDOW_COUNT
TEXTURE_WIDTH = BUFFER_WIDTH
TEXTURE_HEIGHT = BUFFER_HEIGHT


class TextRender(Widget):
    text = StringProperty("")

    def __init__(self, **kwargs):
        EventLoop.ensure_window()
        self.canvas = RenderContext(use_parent_projection=True, use_parent_modelview=True)
        super().__init__(**kwargs)

        self.bind(pos=self.update_canvas)
        self.bind(size=self.update_canvas)

        self._texture = Texture.create(size=(TEXTURE_WIDTH, TEXTURE_HEIGHT))
        self._texture.uvpos = (0.0, 1.0)
        self._texture.uvsize = (1.0, -1.0)
        self._texture.min_filter = "nearest"
        self._texture.mag_filter = "nearest"
        self.update_canvas()

        self.fbind("text", self.texture_update)

    def on_size(self, *args):
        _height = self.width * (BUFFER_HEIGHT / BUFFER_WIDTH)
        if self.height != _height:
            self.height = _height
        else:
            self.texture_update()

    def texture_update(self, *args):
        try:
            buffer = get_array_for_text(self.text)

            arr = array("B", buffer.flatten())
            # now blit the array
            self._texture.blit_buffer(arr, colorfmt="luminance", bufferfmt="ubyte")
        except (ValueError, IndexError):
            # text overflowing the preview buffer: keep the last rendering
            pass

    def update_canvas(self, *args):
        self.canvas.clear()
        wi = BUFFER_WIDTH
        hi = BUFFER_HEIGHT

        ws = self.size[0]
        preview_width = int(ws * 0.20) - 1
        preview_display = (preview_width, hi * preview_width // wi)

        display_width = ws - preview_display[0]
        hi * display_width // wi

        with self.canvas:
            x, y = self.pos
            Color(1, 1, 1, 1)
            Rectangle(texture=self._texture, pos=(x, y), size=self.size)  # (display_width, display_height))

            Color(1, 0, 0, 1)

            window_screen_height = self.size[1] // WINDOW_COUNT

            for k in range(WINDOW_COUNT):
                Rectangle(pos=(self.pos[0], self.pos[1] + (k * window_screen_height)), size=(self.size[0], 2))


class ActionButtonBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = 10
        # self.size_hint = (1., .2)

        self.register_event_type("on_previous")
        self.register_event_type("on_next")
        self.register_event_type("on_discard")
        self.register_event_type("on_save")
        self.register_event_type("on_save_file")
        self.register_event_type("on_next_file")
        self.register_event_type("on_previous_file")

        previous_button = Button(text="Previous")
        next_button = Button(text="Next")
        discard_button = Button(text="Discard")
        save_button = Button(text="Save")
        save_file_button = Button(text="Save File")
        previous_file_button = Button(text="Previous File")
        next_file_button = Button(text="Next File")

        previous_button.bind(on_press=lambda k: self.dispatch("on_previous"))
        next_button.bind(on_press=lambda k: self.dispatch("on_next"))
        discard_button.bind(on_press=lambda k: self.dispatch("on_discard"))
        save_button.bind(on_press=lambda k: self.dispatch("on_save"))
        save_file_button.bind(on_press=lambda k: self.dispatch("on_save_file"))
        previous_file_button.bind(on_press=lambda k: self.dispatch("on_previous_file"))
        next_file_button.bind(on_press=lambda k: self.dispatch("on_next_file"))

        self.add_widget(previous_button)
        self.add_widget(next_button)
        self.add_widget(discard_button)
        self.add_widget(save_button)
        self.add_widget(save_file_button)
        self.add_widget(previous_file_button)
        self.add_widget(next_file_button)

    def on_previous(self):
        pass

    def on_next(self):
        pass

    def on_discard(self):
        pass

    def on_save(self):
        pass

    def on_save_file(self):
        pass

    def on_previous_file(self):
        pass

    def on_next_file(self):
        pass


class DialogEditorApp(App):
    def __init__(self, **kwargs):
        super().__init__()
        # defaults
        self.texts = []
        self.current = ""
        self.current_index = 0
        self.current_file_path = None
        self.tree = None
        self.current_file_index = 0

        self.dialog_dir = kwargs.get("dialog_dir", os.path.join(os.path.dirname(__file__), "../../text/dialog"))
        self.message_files = sorted(os.listdir(self.dialog_dir))

        self.load_current_file()

    def load_current_file(self):
        self.title = self.message_files[self.current_file_index]
        self.current_file_path = os.path.join(self.dialog_dir, self.message_files[self.current_file_index])
        self._load_texts()

    def _load_texts(self):
        self.tree = ET.parse(self.current_file_path)
        self.texts = self.tree.findall("text")
        self.current_index = 0
        self.current = self.texts[self.current_index]

    def save(self):
        with open(self.current_file_path, "wb") as output:
            output.write(ET.tostring(self.tree.getroot(), "utf-8"))

    def build(self):
        action_button_bar = ActionButtonBar(size_hint=(1, None))

        popup = Popup(title="Test popup", auto_dismiss=True)

        def alert(msg):
            popup.content = Label(text=msg)
            popup.open()

        def next_text():
            try:
                self.current = self.texts[self.current_index + 1]
            except IndexError:
                pass
            else:
                self.current_index += 1

            text_input.text = self.current.find("data").text

        def save_text():
            self.current.find("data").text = text_input.text

        def previous_text():
            self.current_index -= 1
            update_current_text()

        def previous_file():
            self.current_index = 0
            self.current_file_index -= 1
            self.load_current_file()
            update_current_text()

        def next_file():
            self.current_index = 0
            self.current_file_index += 1
            self.load_current_file()
            update_current_text()

        def update_current_text():
            self.current = self.texts[self.current_index]
            text_input.text = self.current.find("data").text

        action_button_bar.bind(on_previous=lambda k: previous_text())
        action_button_bar.bind(on_next=lambda k: next_text())
        action_button_bar.bind(on_discard=lambda k: alert("on_discard dispatched"))
        action_button_bar.bind(on_save=lambda k: save_text())
        action_button_bar.bind(on_save_file=lambda k: self.save())
        action_button_bar.bind(on_previous_file=lambda k: previous_file())
        action_button_bar.bind(on_next_file=lambda k: next_file())

        high_layout = BoxLayout(orientation="vertical")

        layout = BoxLayout(orientation="horizontal")
        text_input = TextInput(text="", multiline=True, size_hint=(1, 1))  # , height=500)

        def on_text(instance, value):
            text_render.text = value

        text_render = TextRender(size_hint=(1, None))

        text_input.bind(text=on_text)

        scroll_view = ScrollView(height=500, size_hint=(1, 1))
        scroll_view.add_widget(text_render)

        text_input.text = self.current.find("data").text

        layout.add_widget(text_input)
        layout.add_widget(scroll_view)

        high_layout.add_widget(layout)
        high_layout.add_widget(action_button_bar)
        return high_layout


if __name__ == "__main__":
    DialogEditorApp(room_id=0x1E).run()
