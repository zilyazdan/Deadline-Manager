import os
import json
import pygame
from datetime import datetime, date

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.metrics import dp
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


if getattr(__import__("sys"), "frozen", False):
    DATA_FOLDER = os.path.join(
        os.path.expanduser("~"),
        "LifeSystemManager"
    )
else:
    DATA_FOLDER = os.path.dirname(os.path.abspath(__file__))

os.makedirs(DATA_FOLDER, exist_ok=True)

DATA_PATH = os.path.join(DATA_FOLDER, "deadlines.json")


def resource_path(filename):
    import sys

    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)

    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        filename
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

            for _ in range(40):
                line = Line(
                    width=2
                )
                self.lines.append(line)

            Color(0.20, 0.20, 0.20, 1)

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
            pos=self.update_counter,
            size=self.update_counter
        )

        self.update_counter()

    def update_counter(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size

        width = self.width
        height = self.height

        for index, line in enumerate(self.lines):

            start = -height + index * 25

            x1 = start
            y1 = 0

            x2 = start + height
            y2 = height

            if x1 < 0:
                y1 = -x1
                x1 = 0

            if x2 > width:
                y2 = height - (x2 - width)
                x2 = width

            if (
                x1 < width
                and x2 > 0
                and y1 <= height
                and y2 >= 0
            ):
                line.points = [
                    self.x + x1,
                    self.y + y1,
                    self.x + x2,
                    self.y + y2
                ]
            else:
                line.points = []

        self.border.rectangle = (
            self.x,
            self.y,
            self.width,
            self.height
        )


class DeadlineCard(FloatLayout):

    def __init__(
        self,
        manager,
        deadline,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.manager = manager
        self.deadline = deadline
        self.expanded = False

        self.size_hint_y = None
        self.height = dp(190)

        with self.canvas:
            Color(0.055, 0.055, 0.055, 1)

            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)]
            )

            Color(0.18, 0.18, 0.18, 1)

            self.border = Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(12)
                ),
                width=1
            )

        self.bind(
            pos=self.update_graphics,
            size=self.update_graphics
        )

        self.name_label = Label(
            text=deadline.get("name", ""),
            color=(1, 1, 1, 1),
            font_size=dp(21),
            bold=True,
            size_hint=(1, None),
            height=dp(40),
            pos_hint={
                "x": 0,
                "top": 0.94
            },
            halign="center",
            valign="middle"
        )

        self.name_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(self.name_label)

        self.date_label = Label(
            text=self.get_date_text(),
            color=(0.75, 0.75, 0.75, 1),
            font_size=dp(17),
            size_hint=(1, None),
            height=dp(30),
            pos_hint={
                "x": 0,
                "top": 0.73
            },
            halign="center",
            valign="middle"
        )

        self.date_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(self.date_label)

        self.status_label = Label(
            text="",
            color=(1, 1, 1, 1),
            font_size=dp(15),
            size_hint=(1, None),
            height=dp(48),
            pos_hint={
                "x": 0,
                "top": 0.55
            },
            halign="center",
            valign="middle"
        )

        self.status_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(self.status_label)

        self.pin_button = Button(
            text="UNPIN" if deadline.get("pinned", False) else "PIN",
            font_size=dp(15),
            size_hint=(None, None),
            size=(dp(500), dp(38)),
            pos_hint={
                "center_x": 0.5,
                "y": dp(10)
            },
            background_normal="",
            background_color=(0.12, 0.12, 0.12, 1),
            color=(1, 1, 1, 1)
        )

        self.pin_button.bind(
            on_release=self.toggle_pin
        )

        self.add_widget(self.pin_button)

        self.delete_button = Button(
            text="DELETE",
            font_size=dp(15),
            size_hint=(None, None),
            size=(dp(500), dp(38)),
            pos_hint={
                "center_x": 0.5,
                "y": dp(10)
            },
            background_normal="",
            background_color=(0.55, 0.05, 0.05, 1),
            color=(1, 1, 1, 1),
            opacity=0,
            disabled=True
        )

        self.delete_button.bind(
            on_release=self.delete_deadline
        )

        self.add_widget(self.delete_button)

        self.update_status()

    def update_graphics(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size

        self.border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(12)
        )

    def get_date_text(self):

        try:
            d = date(
                int(self.deadline["year"]),
                int(self.deadline["month"]),
                int(self.deadline["day"])
            )

            return d.strftime("%d/%m/%Y")

        except:
            return ""

    def toggle_pin(self, instance):

        self.deadline["pinned"] = not self.deadline.get(
            "pinned",
            False
        )

        self.manager.save_deadlines()

        self.manager.refresh_deadlines()

    def delete_deadline(self, instance):

        if self.deadline in self.manager.deadlines:

            self.manager.deadlines.remove(
                self.deadline
            )

            self.manager.save_deadlines()

            self.manager.refresh_deadlines()

    def show_delete(self):

        self.expanded = True

        self.height = dp(230)

        self.delete_button.opacity = 1
        self.delete_button.disabled = False

        self.pin_button.opacity = 0
        self.pin_button.disabled = True

    def hide_delete(self):

        self.expanded = False

        self.height = dp(190)

        self.delete_button.opacity = 0
        self.delete_button.disabled = True

        self.pin_button.opacity = 1
        self.pin_button.disabled = False

    def on_touch_down(self, touch):

        if not self.collide_point(
            *touch.pos
        ):
            return False

        if self.delete_button.collide_point(
            *touch.pos
        ):
            return super().on_touch_down(touch)

        if self.pin_button.collide_point(
            *touch.pos
        ):
            return super().on_touch_down(touch)

        if self.expanded:
            self.hide_delete()
        else:
            self.show_delete()

        return True

    def update_status(self):

        try:
            deadline_date = date(
                int(self.deadline["year"]),
                int(self.deadline["month"]),
                int(self.deadline["day"])
            )
        except:
            return

        today = date.today()

        difference = (
            deadline_date - today
        ).days

        if difference < 0:

            days = abs(difference)

            if days == 1:
                message = (
                    "OVERDUE\n"
                    "Deadline finished 1 day ago."
                )
            else:
                message = (
                    "OVERDUE\n"
                    f"Deadline finished {days} days ago."
                )

            self.status_label.text = message
            self.status_label.color = (
                1,
                0.25,
                0.25,
                1
            )

        elif difference == 0:

            self.status_label.text = (
                "⚠ Today is last date!\n"
                + self.get_time_left()
            )

            self.status_label.color = (
                1,
                0.35,
                0.35,
                1
            )

        elif difference == 1:

            self.status_label.text = (
                "⚠ Deadline is tomorrow!\n"
                + self.get_time_left()
            )

            self.status_label.color = (
                1,
                0.75,
                0.15,
                1
            )

        elif difference == 2:

            self.status_label.text = (
                "⚠ Deadline is near!\n"
                + self.get_time_left()
            )

            self.status_label.color = (
                1,
                0.75,
                0.15,
                1
            )

        else:

            self.status_label.text = (
                "Deadline is not near.\n"
                + self.get_time_left()
            )

            self.status_label.color = (
                0.75,
                0.75,
                0.75,
                1
            )

    def get_time_left(self):

        try:
            deadline_datetime = datetime(
                int(self.deadline["year"]),
                int(self.deadline["month"]),
                int(self.deadline["day"]),
                23,
                59,
                59
            )

            now = datetime.now()

            difference = (
                deadline_datetime - now
            )

            total_seconds = int(
                difference.total_seconds()
            )

            if total_seconds <= 0:
                return "Deadline time has passed."

            days = total_seconds // 86400

            remaining = total_seconds % 86400

            hours = remaining // 3600

            remaining %= 3600

            minutes = remaining // 60

            seconds = remaining % 60

            return (
                f"Time left : "
                f"{days}d "
                f"{hours}h "
                f"{minutes} mins "
                f"{seconds}s"
            )

        except:
            return ""


class DeadlineManager(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.deadlines = []
        self.cards = []

        self.load_deadlines()

    def build(self):

        Window.bind(
            on_key_down=self.on_key_down
        )

        self.main_layout = FloatLayout()

        self.page = FloatLayout(
            size_hint=(1, 1)
        )

        self.main_layout.add_widget(
            self.page
        )

        self.create_main_page()

        Clock.schedule_interval(
            self.update_countdowns,
            1
        )

        return self.main_layout

    def load_deadlines(self):

        try:
            with open(
                DATA_PATH,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

                if isinstance(data, list):
                    self.deadlines = data
                else:
                    self.deadlines = []

        except (
            FileNotFoundError,
            json.JSONDecodeError
        ):
            self.deadlines = []

    def save_deadlines(self):

        with open(
            DATA_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.deadlines,
                file,
                indent=4
            )

    def create_main_page(self):

        self.page.clear_widgets()

        root = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[
                dp(30),
                dp(20),
                dp(30),
                dp(20)
            ]
        )

        title = Label(
            text="LIFE SYSTEM MANAGER",
            font_size=dp(28),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(45)
        )

        root.add_widget(title)

        self.search = TextInput(
            hint_text="Search deadlines...",
            multiline=False,
            size_hint_y=None,
            height=dp(42),
            padding=[
                dp(12),
                dp(10)
            ],
            background_normal="",
            background_color=(0.08, 0.08, 0.08, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1)
        )

        self.search.bind(
            text=self.search_deadlines
        )

        root.add_widget(self.search)

        counter_box = FloatLayout(
            size_hint_y=None,
            height=dp(100),
            size_hint_x=None,
            width=dp(500),
            pos_hint={
                "center_x": 0.5
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
            text=(
                f"TOTAL DEADLINES: "
                f"{len(self.deadlines)}"
            ),
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

        add_button = Button(
            text="ADD DEADLINE",
            font_size=dp(17),
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=(
                0.10,
                0.10,
                0.10,
                1
            ),
            color=(1, 1, 1, 1)
        )

        add_button.bind(
            on_release=self.show_add_page
        )

        root.add_widget(add_button)

        your_deadlines = Label(
            text="YOUR DEADLINES",
            font_size=dp(22),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(40)
        )

        root.add_widget(
            your_deadlines
        )

        self.scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True
        )

        self.deadline_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[
                0,
                dp(5),
                0,
                dp(20)
            ],
            size_hint_y=None
        )

        self.deadline_layout.bind(
            minimum_height=
            self.deadline_layout.setter(
                "height"
            )
        )

        self.scroll.add_widget(
            self.deadline_layout
        )

        root.add_widget(
            self.scroll
        )

        self.page.add_widget(root)

        self.refresh_deadlines()

    def refresh_deadlines(self, *args):

        if not hasattr(
            self,
            "deadline_layout"
        ):
            return

        search_text = ""

        if hasattr(
            self,
            "search"
        ):
            search_text = (
                self.search.text
                .strip()
                .casefold()
            )

        filtered = []

        for deadline in self.deadlines:

            name = deadline.get(
                "name",
                ""
            )

            if (
                not search_text
                or search_text in name.casefold()
            ):
                filtered.append(
                    deadline
                )

        filtered.sort(
            key=lambda item:
            not item.get(
                "pinned",
                False
            )
        )

        self.deadline_layout.clear_widgets()

        self.cards = []

        for deadline in filtered:

            card = DeadlineCard(
                self,
                deadline
            )

            self.cards.append(card)

            self.deadline_layout.add_widget(
                card
            )

        if hasattr(
            self,
            "counter_label"
        ):

            self.counter_label.text = (
                f"TOTAL DEADLINES: "
                f"{len(self.deadlines)}"
            )

    def search_deadlines(self, *args):

        self.refresh_deadlines()

    def update_countdowns(self, *args):

        for card in self.cards:

            if card.parent:

                card.update_status()

        self.check_alerts()

    def check_alerts(self):

        today = date.today()

        for deadline in self.deadlines:

            try:

                deadline_date = date(
                    int(deadline["year"]),
                    int(deadline["month"]),
                    int(deadline["day"])
                )

            except:
                continue

            difference = (
                deadline_date - today
            ).days

            name = deadline.get(
                "name",
                "Deadline"
            )

            alert_key = (
                f"{name}_"
                f"{deadline['day']}_"
                f"{deadline['month']}_"
                f"{deadline['year']}"
            )

            if difference == 1:

                if deadline.get(
                    "tomorrow_alert_sent",
                    False
                ):
                    continue

                self.play_alarm()

                self.send_notification(
                    "Life System Manager",
                    "Hello from Life System Manager. "
                    f"The deadline ({name}) "
                    "is scheduled to conclude tomorrow."
                )

                deadline[
                    "tomorrow_alert_sent"
                ] = True

                self.save_deadlines()

            elif difference == 0:

                if deadline.get(
                    "today_alert_sent",
                    False
                ):
                    continue

                self.play_alarm()

                self.send_notification(
                    "Life System Manager",
                    "Hello from Life System Manager. "
                    f"The deadline ({name}) "
                    "is due today. "
                    "We hope you have completed "
                    "the deadline."
                )

                deadline[
                    "today_alert_sent"
                ] = True

                self.save_deadlines()

    def play_alarm(self):

        try:

            sound_path = resource_path(
                "Alarm Sound Effect.mp3"
            )

            if os.path.exists(sound_path):

                pygame.mixer.init()

                pygame.mixer.music.load(
                    sound_path
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

    def show_add_page(self, instance):

        self.page.clear_widgets()

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(15),
            padding=[
                dp(100),
                dp(40),
                dp(100),
                dp(40)
            ]
        )

        title = Label(
            text="ADD DEADLINE",
            font_size=dp(30),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(60)
        )

        layout.add_widget(title)

        self.name_input = TextInput(
            hint_text="Deadline Name",
            multiline=False,
            size_hint_y=None,
            height=dp(45),
            background_normal="",
            background_color=(0.08, 0.08, 0.08, 1),
            foreground_color=(1, 1, 1, 1)
        )

        layout.add_widget(
            self.name_input
        )

        date_box = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(45)
        )

        self.day_input = TextInput(
            hint_text="Day",
            multiline=False,
            input_filter="int",
            background_normal="",
            background_color=(0.08, 0.08, 0.08, 1),
            foreground_color=(1, 1, 1, 1)
        )

        self.month_input = TextInput(
            hint_text="Month",
            multiline=False,
            input_filter="int",
            background_normal="",
            background_color=(0.08, 0.08, 0.08, 1),
            foreground_color=(1, 1, 1, 1)
        )

        self.year_input = TextInput(
            hint_text="Year",
            multiline=False,
            input_filter="int",
            background_normal="",
            background_color=(0.08, 0.08, 0.08, 1),
            foreground_color=(1, 1, 1, 1)
        )

        date_box.add_widget(
            self.day_input
        )

        date_box.add_widget(
            self.month_input
        )

        date_box.add_widget(
            self.year_input
        )

        layout.add_widget(date_box)

        self.error_label = Label(
            text="",
            color=(1, 0.25, 0.25, 1),
            font_size=dp(15),
            size_hint_y=None,
            height=dp(45)
        )

        layout.add_widget(
            self.error_label
        )

        add_button = Button(
            text="CREATE DEADLINE",
            font_size=dp(17),
            size_hint_y=None,
            height=dp(50),
            background_normal="",
            background_color=(
                0.10,
                0.10,
                0.10,
                1
            )
        )

        add_button.bind(
            on_release=self.add_deadline
        )

        layout.add_widget(
            add_button
        )

        back_button = Button(
            text="GO BACK",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(45),
            background_normal="",
            background_color=(
                0.07,
                0.07,
                0.07,
                1
            )
        )

        back_button.bind(
            on_release=self.create_main_page
        )

        layout.add_widget(
            back_button
        )

        self.page.add_widget(
            layout
        )

    def add_deadline(self, instance):

        name = self.name_input.text.strip()

        day_text = self.day_input.text.strip()
        month_text = self.month_input.text.strip()
        year_text = self.year_input.text.strip()

        if not name:

            self.error_label.text = (
                "Please enter a deadline name."
            )

            return

        if (
            not day_text
            or not month_text
            or not year_text
        ):

            self.error_label.text = (
                "Please enter a complete date."
            )

            return

        try:

            day = int(day_text)
            month = int(month_text)
            year = int(year_text)

            deadline_date = date(
                year,
                month,
                day
            )

        except:

            self.error_label.text = (
                "Please enter a valid date."
            )

            return

        if deadline_date < date.today():

            self.error_label.text = (
                "Please enter a valid date."
            )

            return

        for deadline in self.deadlines:

            same_name = (
                deadline.get(
                    "name",
                    ""
                ).casefold()
                == name.casefold()
            )

            same_date = (
                int(
                    deadline.get(
                        "day",
                        0
                    )
                ) == day
                and
                int(
                    deadline.get(
                        "month",
                        0
                    )
                ) == month
                and
                int(
                    deadline.get(
                        "year",
                        0
                    )
                ) == year
            )

            if same_name and same_date:

                self.error_label.text = (
                    "You have already created "
                    "this deadline."
                )

                return

        new_deadline = {
            "name": name,
            "day": day,
            "month": month,
            "year": year,
            "pinned": False,
            "tomorrow_alert_sent": False,
            "today_alert_sent": False
        }

        self.deadlines.append(
            new_deadline
        )

        self.save_deadlines()

        self.create_main_page()

    def on_key_down(
        self,
        window,
        key,
        scancode,
        codepoint,
        modifiers
    ):

        if key == 27:

            self.create_main_page()

            return True

        return False

    def on_stop(self):

        try:
            pygame.mixer.quit()
        except:
            pass


if __name__ == "__main__":
    DeadlineManager().run()
