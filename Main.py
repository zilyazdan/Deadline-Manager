import os
import json
import pygame
from datetime import datetime, date

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

try:
    from plyer import notification
except:
    notification = None


Window.size = (900, 600)
Window.clearcolor = (0, 0, 0, 1)


BASE_PATH = os.path.dirname(os.path.abspath(__file__))

if getattr(__import__("sys"), "frozen", False):
    DATA_PATH = os.path.join(
        os.path.expanduser("~"),
        "LifeSystemManager"
    )
    os.makedirs(DATA_PATH, exist_ok=True)
else:
    DATA_PATH = BASE_PATH

SAVE_PATH = os.path.join(
    DATA_PATH,
    "deadlines.json"
)

SOUND_PATH = os.path.join(
    BASE_PATH,
    "Alarm Sound Effect.mp3"
)

ICON_PATH = os.path.join(
    BASE_PATH,
    "Icon.png"
)


class StripeCounter(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(0.067, 0.067, 0.067, 1)
            self.background = Rectangle(
                pos=self.pos,
                size=self.size
            )

            Color(0.145, 0.145, 0.145, 1)

            self.lines = []

            for x in range(-100, 700, 25):
                line = Line(
                    points=[
                        self.x + x,
                        self.y,
                        self.x + x + 100,
                        self.y + 100
                    ],
                    width=1.5
                )

                self.lines.append(line)

            Color(0.25, 0.25, 0.25, 1)

            self.border = Line(
                rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height
                ),
                width=1
            )

        self.bind(
            pos=self.update_graphics,
            size=self.update_graphics
        )

    def update_graphics(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size

        for index, line in enumerate(self.lines):

            x = -100 + index * 25

            line.points = [
                self.x + x,
                self.y,
                self.x + x + 100,
                self.y + 100
            ]

        self.border.rectangle = (
            self.x,
            self.y,
            self.width,
            self.height
        )


class DeadlineCard(FloatLayout):

    expanded = BooleanProperty(False)

    def __init__(
        self,
        manager,
        deadline,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.manager = manager
        self.deadline = deadline

        self.size_hint_y = None
        self.height = dp(185)

        with self.canvas.before:
            Color(
                0.09,
                0.09,
                0.09,
                1
            )

            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8)]
            )

            Color(
                0.20,
                0.20,
                0.20,
                1
            )

            self.border = Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(8)
                ),
                width=1
            )

        self.bind(
            pos=self.update_graphics,
            size=self.update_graphics
        )

        self.name_label = Label(
            text=deadline.get("name", ""),
            font_size=dp(17),
            bold=True,
            color=(1, 1, 1, 1),
            halign="left",
            valign="middle",
            size_hint=(1, None),
            height=dp(38),
            pos_hint={
                "x": 0,
                "top": 1
            },
            padding=(dp(15), 0)
        )

        self.date_label = Label(
            text=f"Date: {deadline.get('date', '')}",
            font_size=dp(13),
            color=(0.67, 0.67, 0.67, 1),
            halign="left",
            valign="middle",
            size_hint=(1, None),
            height=dp(28),
            pos_hint={
                "x": 0,
                "top": 0.78
            },
            padding=(dp(15), 0)
        )

        self.status_label = Label(
            text="",
            font_size=dp(13),
            bold=True,
            color=(0, 1, 0, 1),
            halign="left",
            valign="middle",
            text_size=(None, None),
            size_hint=(1, None),
            height=dp(58),
            pos_hint={
                "x": 0,
                "top": 0.63
            },
            padding=(dp(15), 0)
        )

        self.pin_button = Button(
            text="",
            font_size=dp(12),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(38),
            pos_hint={
                "x": 0,
                "y": 0
            },
            background_normal="",
            background_down="",
            border=(0, 0, 0, 0)
        )

        self.pin_button.bind(
            on_release=self.pin_pressed
        )

        self.delete_button = Button(
            text="DELETE DEADLINE",
            font_size=dp(12),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(38),
            pos_hint={
                "x": 0,
                "y": 0
            },
            background_normal="",
            background_down="",
            border=(0, 0, 0, 0)
        )

        self.delete_button.bind(
            on_release=self.delete_pressed
        )

        self.add_widget(
            self.name_label
        )

        self.add_widget(
            self.date_label
        )

        self.add_widget(
            self.status_label
        )

        self.add_widget(
            self.pin_button
        )

        self.refresh_visuals()

        self.delete_button.opacity = 0
        self.delete_button.disabled = True

        self.update_status()

    def update_graphics(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size

        self.border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(8)
        )

    def on_touch_down(self, touch):

        if not self.collide_point(
            *touch.pos
        ):
            return super().on_touch_down(touch)

        if (
            touch.pos[1]
            >= self.y
            and touch.pos[1]
            <= self.y + dp(38)
        ):
            return super().on_touch_down(touch)

        if (
            touch.pos[1]
            >= self.y + dp(38)
            and touch.pos[1]
            <= self.top
        ):
            self.toggle_delete()

            return True

        return super().on_touch_down(touch)

    def toggle_delete(self):

        self.expanded = not self.expanded

        if self.expanded:

            self.height = dp(230)

            self.delete_button.pos_hint = {
                "x": 0,
                "y": 0
            }

            self.delete_button.opacity = 1
            self.delete_button.disabled = False

            self.pin_button.pos_hint = {
                "x": 0,
                "y": dp(42)
            }

        else:

            self.height = dp(185)

            self.delete_button.opacity = 0
            self.delete_button.disabled = True

            self.pin_button.pos_hint = {
                "x": 0,
                "y": 0
            }

    def pin_pressed(self, instance):

        self.manager.toggle_pin(
            self.deadline
        )

    def delete_pressed(self, instance):

        self.manager.delete_deadline(
            self.deadline
        )

    def refresh_visuals(self):

        if self.deadline.get(
            "pinned",
            False
        ):

            self.pin_button.text = "UNPIN"
            self.pin_button.background_color = (
                0.50,
                0.38,
                0,
                1
            )

        else:

            self.pin_button.text = "PIN"
            self.pin_button.background_color = (
                0.20,
                0.20,
                0.20,
                1
            )

        self.name_label.text = self.deadline.get(
            "name",
            ""
        )

        self.date_label.text = (
            f"Date: {self.deadline.get('date', '')}"
        )

    def update_status(self):

        try:

            deadline_date = datetime.strptime(
                self.deadline["date"],
                "%d/%m/%Y"
            ).date()

        except:

            self.status_label.text = (
                "Invalid date"
            )

            self.status_label.color = (
                1,
                0,
                0,
                1
            )

            return

        today = datetime.now().date()

        difference = (
            deadline_date - today
        ).days

        pinned_text = (
            "\nPinned 📌"
            if self.deadline.get(
                "pinned",
                False
            )
            else "\nNot pinned"
        )

        if difference < 0:

            days_ago = abs(
                difference
            )

            if days_ago == 1:
                time_text = "1 day ago"
            else:
                time_text = (
                    f"{days_ago} days ago"
                )

            self.status_label.text = (
                "OVERDUE\n"
                f"Deadline finished {time_text}."
                f"{pinned_text}"
            )

            self.status_label.color = (
                1,
                0,
                0,
                1
            )

        elif difference == 2:

            self.status_label.text = (
                "⚠ Deadline is near!\n"
                "Days Remaining : 2"
                f"{pinned_text}"
            )

            self.status_label.color = (
                1,
                0.55,
                0,
                1
            )

        elif difference == 1:

            self.status_label.text = (
                "⚠ Deadline is tomorrow!\n"
                "Days Remaining : 1"
                f"{pinned_text}"
            )

            self.status_label.color = (
                1,
                0.55,
                0,
                1
            )

        elif difference == 0:

            self.status_label.text = (
                "⚠ Today is last date!"
                f"{pinned_text}"
            )

            self.status_label.color = (
                1,
                0,
                0,
                1
            )

        else:

            self.status_label.text = (
                "Deadline is not near.\n"
                f"Days Remaining : {difference}"
                f"{pinned_text}"
            )

            self.status_label.color = (
                0,
                1,
                0,
                1
            )


class DeadlineManager(App):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.deadlines = []

        self.cards = {}

        self.alerted_tomorrow = set()

        self.alerted_today = set()

        self.last_search = ""

        self.add_form_visible = False

    def build(self):

        self.load_deadlines()

        if os.path.exists(
            ICON_PATH
        ):

            self.icon = ICON_PATH

        self.main_layout = FloatLayout()

        self.build_interface()

        Clock.schedule_interval(
            self.update_countdowns,
            1
        )

        return self.main_layout

    def load_deadlines(self):

        if not os.path.exists(
            SAVE_PATH
        ):

            self.deadlines = []

            return

        try:

            with open(
                SAVE_PATH,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if isinstance(
                data,
                list
            ):

                self.deadlines = data

            else:

                self.deadlines = []

        except:

            self.deadlines = []

        for deadline in self.deadlines:

            if "pinned" not in deadline:

                deadline["pinned"] = False

    def save_deadlines(self):

        try:

            with open(
                SAVE_PATH,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.deadlines,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

        except:

            pass

    def build_interface(self):

        self.main_layout.clear_widgets()

        root = FloatLayout()

        self.main_layout.add_widget(
            root
        )

        title = Label(
            text="DEADLINE MANAGER",
            font_size=dp(30),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(55),
            pos_hint={
                "x": 0,
                "top": 0.98
            }
        )

        root.add_widget(
            title
        )

        self.search_entry = TextInput(
            hint_text="Search deadlines...",
            multiline=False,
            font_size=dp(15),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.55, 0.55, 0.55, 1),
            background_color=(0.09, 0.09, 0.09, 1),
            cursor_color=(1, 1, 1, 1),
            padding=[
                dp(12),
                dp(10)
            ],
            size_hint=(None, None),
            width=dp(400),
            height=dp(45),
            pos_hint={
                "center_x": 0.5,
                "top": 0.88
            }
        )

        self.search_entry.bind(
            text=self.search_changed
        )

        root.add_widget(
            self.search_entry
        )

        counter_box = FloatLayout(
            size_hint=(None, None),
            width=dp(500),
            height=dp(100),
            pos_hint={
                "center_x": 0.5,
                "top": 0.77
            }
        )

        stripe_background = StripeCounter(
            size_hint=(1, 1),
            pos_hint={
                "x": 0,
                "y": 0
            }
        )

        counter_box.add_widget(
            stripe_background
        )

        self.counter_label = Label(
            text="",
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, 1),
            pos_hint={
                "x": 0,
                "y": 0
            },
            halign="center",
            valign="middle"
        )

        self.counter_label.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        counter_box.add_widget(
            self.counter_label
        )

        root.add_widget(
            counter_box
        )

        self.form_area = FloatLayout(
            size_hint=(1, None),
            height=dp(210),
            pos_hint={
                "x": 0,
                "top": 0.61
            }
        )

        root.add_widget(
            self.form_area
        )

        self.add_button = Button(
            text="ADD DEADLINE",
            font_size=dp(14),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            width=dp(230),
            height=dp(50),
            pos_hint={
                "center_x": 0.5,
                "top": 0.95
            },
            background_normal="",
            background_color=(
                0.13,
                0.13,
                0.13,
                1
            )
        )

        self.add_button.bind(
            on_release=self.show_add_form
        )

        self.form_area.add_widget(
            self.add_button
        )

        self.create_form_widgets()

        self.your_deadlines = Label(
            text="YOUR DEADLINES",
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(40),
            pos_hint={
                "x": 0,
                "top": 0.48
            }
        )

        root.add_widget(
            self.your_deadlines
        )

        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(8),
            size_hint=(None, None),
            width=dp(820),
            height=dp(220),
            pos_hint={
                "center_x": 0.5,
                "y": 0.03
            }
        )

        self.deadline_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[
                dp(10),
                dp(5),
                dp(10),
                dp(5)
            ],
            size_hint_y=None
        )

        self.deadline_layout.bind(
            minimum_height=self.deadline_layout.setter(
                "height"
            )
        )

        self.scroll_view.add_widget(
            self.deadline_layout
        )

        root.add_widget(
            self.scroll_view
        )

        self.refresh_deadlines(
            preserve_cards=False
        )

    def create_form_widgets(self):

        self.name_input = TextInput(
            hint_text="Deadline Name",
            multiline=False,
            font_size=dp(14),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.55, 0.55, 0.55, 1),
            background_color=(0.09, 0.09, 0.09, 1),
            padding=[
                dp(10),
                dp(8)
            ],
            size_hint=(None, None),
            width=dp(350),
            height=dp(40),
            pos_hint={
                "center_x": 0.5,
                "top": 0.95
            }
        )

        self.day_input = TextInput(
            hint_text="Day",
            multiline=False,
            input_filter="int",
            font_size=dp(14),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.55, 0.55, 0.55, 1),
            background_color=(0.09, 0.09, 0.09, 1),
            padding=[
                dp(10),
                dp(8)
            ],
            size_hint=(None, None),
            width=dp(100),
            height=dp(40),
            pos_hint={
                "center_x": 0.5,
                "top": 0.75
            }
        )

        self.month_input = TextInput(
            hint_text="Month",
            multiline=False,
            input_filter="int",
            font_size=dp(14),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.55, 0.55, 0.55, 1),
            background_color=(0.09, 0.09, 0.09, 1),
            padding=[
                dp(10),
                dp(8)
            ],
            size_hint=(None, None),
            width=dp(100),
            height=dp(40),
            pos_hint={
                "center_x": 0.5,
                "top": 0.55
            }
        )

        self.year_input = TextInput(
            hint_text="Year",
            multiline=False,
            input_filter="int",
            font_size=dp(14),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.55, 0.55, 0.55, 1),
            background_color=(0.09, 0.09, 0.09, 1),
            padding=[
                dp(10),
                dp(8)
            ],
            size_hint=(None, None),
            width=dp(100),
            height=dp(40),
            pos_hint={
                "center_x": 0.5,
                "top": 0.35
            }
        )

        self.result_label = Label(
            text="",
            font_size=dp(13),
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(30),
            pos_hint={
                "center_x": 0.5,
                "top": 0.18
            }
        )

        self.create_button = Button(
            text="CREATE DEADLINE",
            font_size=dp(13),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            width=dp(220),
            height=dp(42),
            pos_hint={
                "center_x": 0.5,
                "top": 0.03
            },
            background_normal="",
            background_color=(
                0.20,
                0.20,
                0.20,
                1
            )
        )

        self.create_button.bind(
            on_release=self.add_deadline
        )

        self.back_button = Button(
            text="BACK",
            font_size=dp(13),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            width=dp(150),
            height=dp(42),
            pos_hint={
                "center_x": 0.5,
                "top": -0.10
            },
            background_normal="",
            background_color=(
                0.13,
                0.13,
                0.13,
                1
            )
        )

        self.back_button.bind(
            on_release=self.hide_add_form
        )

        self.form_widgets = [
            self.name_input,
            self.day_input,
            self.month_input,
            self.year_input,
            self.result_label,
            self.create_button,
            self.back_button
        ]

        for widget in self.form_widgets:

            widget.opacity = 0
            widget.disabled = True

            self.form_area.add_widget(
                widget
            )

    def show_add_form(self, instance=None):

        self.add_form_visible = True

        self.add_button.opacity = 0
        self.add_button.disabled = True

        for widget in self.form_widgets:

            widget.opacity = 1
            widget.disabled = False

        self.name_input.focus = True

    def hide_add_form(self, instance=None):

        self.add_form_visible = False

        self.add_button.opacity = 1
        self.add_button.disabled = False

        for widget in self.form_widgets:

            widget.opacity = 0
            widget.disabled = True

        self.name_input.text = ""
        self.day_input.text = ""
        self.month_input.text = ""
        self.year_input.text = ""

        self.result_label.text = ""

        self.name_input.focus = False

    def add_deadline(self, instance=None):

        name = self.name_input.text.strip()
        day = self.day_input.text.strip()
        month = self.month_input.text.strip()
        year = self.year_input.text.strip()

        if (
            name == ""
            or day == ""
            or month == ""
            or year == ""
        ):

            self.result_label.text = (
                "Please fill in all fields."
            )

            self.result_label.color = (
                1,
                0.55,
                0,
                1
            )

            return

        try:

            deadline_date = datetime(
                int(year),
                int(month),
                int(day)
            )

        except:

            self.result_label.text = (
                "Please enter a valid date."
            )

            self.result_label.color = (
                1,
                0.55,
                0,
                1
            )

            return

        if (
            deadline_date.date()
            < datetime.now().date()
        ):

            self.result_label.text = (
                "Please enter a valid date."
            )

            self.result_label.color = (
                1,
                0.55,
                0,
                1
            )

            return

        formatted_date = (
            deadline_date.strftime(
                "%d/%m/%Y"
            )
        )

        for existing in self.deadlines:

            if (
                existing.get(
                    "name",
                    ""
                ).casefold()
                == name.casefold()
                and existing.get(
                    "date",
                    ""
                )
                == formatted_date
            ):

                self.result_label.text = (
                    "You have already created "
                    "this deadline."
                )

                self.result_label.color = (
                    1,
                    0,
                    0,
                    1
                )

                return

        self.deadlines.append(
            {
                "name": name,
                "date": formatted_date,
                "pinned": False
            }
        )

        self.save_deadlines()

        self.refresh_deadlines(
            preserve_cards=False
        )

        self.hide_add_form()

    def pinned_deadlines(self):

        for deadline in self.deadlines:

            if "pinned" not in deadline:

                deadline["pinned"] = False

        self.deadlines.sort(
            key=lambda deadline:
            deadline.get(
                "pinned",
                False
            ),
            reverse=True
        )

    def toggle_pin(self, deadline):

        deadline["pinned"] = not deadline.get(
            "pinned",
            False
        )

        self.save_deadlines()

        self.refresh_deadlines(
            preserve_cards=False
        )

    def delete_deadline(self, deadline):

        if deadline in self.deadlines:

            self.deadlines.remove(
                deadline
            )

        self.save_deadlines()

        self.refresh_deadlines(
            preserve_cards=False
        )

    def search_changed(self, instance, value):

        value = value.casefold()

        if value == self.last_search:
            return

        self.last_search = value

        self.refresh_deadlines(
            preserve_cards=False
        )

    def refresh_deadlines(
        self,
        preserve_cards=True
    ):

        self.pinned_deadlines()

        search_text = (
            self.search_entry.text.strip().casefold()
        )

        if search_text == "":
            search_text = ""

        visible_deadlines = []

        for deadline in self.deadlines:

            name = deadline.get(
                "name",
                ""
            )

            deadline_date = deadline.get(
                "date",
                ""
            )

            if (
                search_text not in name.casefold()
                and search_text not in deadline_date.casefold()
            ):
                continue

            visible_deadlines.append(
                deadline
            )

        if not preserve_cards:

            self.deadline_layout.clear_widgets()

            self.cards.clear()

            for deadline in visible_deadlines:

                card = DeadlineCard(
                    self,
                    deadline
                )

                self.cards[id(deadline)] = card

                self.deadline_layout.add_widget(
                    card
                )

        else:

            for deadline in visible_deadlines:

                card = self.cards.get(
                    id(deadline)
                )

                if card is not None:

                    card.update_status()
                    card.refresh_visuals()

        self.counter_label.text = (
            f"TOTAL DEADLINES: "
            f"{len(self.deadlines)}"
        )

    def update_countdowns(self, dt):

        self.check_deadline_alerts()

        for deadline in self.deadlines:

            card = self.cards.get(
                id(deadline)
            )

            if card is not None:

                card.update_status()

                card.refresh_visuals()

    def check_deadline_alerts(self):

        today = datetime.now().date()

        for deadline in self.deadlines:

            try:

                deadline_date = datetime.strptime(
                    deadline["date"],
                    "%d/%m/%Y"
                ).date()

            except:

                continue

            difference = (
                deadline_date - today
            ).days

            identifier = (
                f"{deadline.get('name', '')}"
                f"|{deadline.get('date', '')}"
            )

            if difference == 1:

                if identifier not in self.alerted_tomorrow:

                    self.play_sound()

                    self.send_notification(
                        "Hello from Life System Manager",
                        (
                            "The deadline "
                            f"({deadline.get('name', '')}) "
                            "is scheduled to conclude "
                            "tomorrow."
                        )
                    )

                    self.alerted_tomorrow.add(
                        identifier
                    )

            elif difference == 0:

                if identifier not in self.alerted_today:

                    self.send_notification(
                        "Hello from Life System Manager",
                        (
                            "The deadline "
                            f"({deadline.get('name', '')}) "
                            "is due today. "
                            "We hope you have completed "
                            "the deadline."
                        )
                    )

                    self.alerted_today.add(
                        identifier
                    )

    def play_sound(self):

        if not os.path.exists(
            SOUND_PATH
        ):

            return

        try:

            if not pygame.mixer.get_init():

                pygame.mixer.init()

            pygame.mixer.music.load(
                SOUND_PATH
            )

            pygame.mixer.music.play()

        except:

            pass

    def send_notification(
        self,
        title,
        message
    ):

        if notification is None:

            return

        try:

            notification.notify(
                title=title,
                message=message,
                app_name="Life System Manager",
                timeout=10
            )

        except:

            pass


if __name__ == "__main__":

    DeadlineManager().run()
