import os
import json
import pygame

from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

try:
    from plyer import notification
except:
    notification = None


Window.size = (900, 600)
Window.minimum_width = 900
Window.minimum_height = 600
Window.maximum_width = 900
Window.maximum_height = 600
Window.clearcolor = (0, 0, 0, 1)


class StripeCounter(Widget):
    def __init__(self, **kwargs):
        self.stripes = []
        super().__init__(**kwargs)

        with self.canvas:
            Color(0.067, 0.067, 0.067, 1)
            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8)]
            )

            Color(0.145, 0.145, 0.145, 1)

        self.bind(
            pos=self.update_graphics,
            size=self.update_graphics
        )

        self.draw_stripes()

    def update_graphics(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size
        self.draw_stripes()

    def draw_stripes(self):
        for stripe in self.stripes:
            self.canvas.remove(stripe)

        self.stripes = []

        with self.canvas:
            Color(0.145, 0.145, 0.145, 1)

            start = int(-self.height)

            end = int(self.width + self.height)

            for x in range(start, end, 25):
                stripe = Line(
                    points=[
                        self.x + x,
                        self.y,
                        self.x + x + self.height,
                        self.y + self.height
                    ],
                    width=1.5
                )

                self.stripes.append(stripe)


class DeadlineCard(BoxLayout):
    def __init__(
        self,
        deadline,
        status_text,
        status_color,
        pin_callback,
        delete_callback,
        **kwargs
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(3),
            padding=[dp(15), dp(10), dp(15), dp(10)],
            **kwargs
        )

        self.deadline = deadline
        self.pin_callback = pin_callback
        self.delete_callback = delete_callback

        self.card_height = dp(185)
        self.closed_height = dp(145)

        self.height = self.closed_height

        with self.canvas.before:
            Color(0.09, 0.09, 0.09, 1)
            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(6)]
            )

            Color(0.20, 0.20, 0.20, 1)
            self.border = Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(6)
                ),
                width=1
            )

        self.bind(
            pos=self.update_background,
            size=self.update_background
        )

        name_label = Label(
            text=deadline["name"],
            color=(1, 1, 1, 1),
            font_size=dp(16),
            bold=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(30)
        )

        name_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        date_label = Label(
            text=f"Date: {deadline['date']}",
            color=(0.67, 0.67, 0.67, 1),
            font_size=dp(12),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(25)
        )

        date_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.status_label = Label(
            text=status_text,
            color=status_color,
            font_size=dp(12),
            bold=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(45)
        )

        self.status_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(name_label)
        self.add_widget(date_label)
        self.add_widget(self.status_label)

        button_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(35),
            spacing=dp(8)
        )

        pin_button = Button(
            text="UNPIN"
            if deadline.get("pinned", False)
            else "PIN",
            font_size=dp(10),
            bold=True,
            color=(1, 1, 1, 1),
            background_normal="",
            background_color=(
                (0.50, 0.38, 0, 1)
                if deadline.get("pinned", False)
                else (0.20, 0.20, 0.20, 1)
            )
        )

        pin_button.bind(
            on_release=lambda instance:
            self.pin_callback(self.deadline)
        )

        self.delete_button = Button(
            text="DELETE DEADLINE",
            font_size=dp(11),
            bold=True,
            color=(1, 1, 1, 1),
            background_normal="",
            background_color=(0.40, 0.07, 0.07, 1),
            opacity=0,
            disabled=True
        )

        self.delete_button.bind(
            on_release=lambda instance:
            self.delete_callback(self.deadline)
        )

        button_layout.add_widget(pin_button)
        button_layout.add_widget(self.delete_button)

        self.add_widget(button_layout)

        self.bind(
            on_touch_down=self.card_touch
        )

    def update_background(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size

        self.border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(6)
        )

    def card_touch(self, instance, touch):
        if not self.collide_point(*touch.pos):
            return False

        if touch.button not in (None, "left"):
            return False

        if self.delete_button.opacity == 0:
            self.delete_button.opacity = 1
            self.delete_button.disabled = False
            self.height = self.card_height
        else:
            self.delete_button.opacity = 0
            self.delete_button.disabled = True
            self.height = self.closed_height

        return False


class DeadlineManager(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.deadlines = []

        self.base_path = os.path.dirname(
            os.path.abspath(__file__)
        )

        self.save_path = os.path.join(
            self.base_path,
            "deadlines.json"
        )

        self.sound_path = os.path.join(
            self.base_path,
            "Alarm Sound Effect.mp3"
        )

        self.main_layout = None
        self.deadline_display = None
        self.counter_label = None
        self.search_entry = None

        self.form_layout = None
        self.name_entry = None
        self.day_entry = None
        self.month_entry = None
        self.year_entry = None
        self.result_label = None

        self.add_button = None
        self.back_button = None

        self.notification_sent = set()
        self.sound_played = set()

    def build(self):
        if os.path.exists(
            os.path.join(self.base_path, "Icon.png")
        ):
            Window.set_icon(
                os.path.join(
                    self.base_path,
                    "Icon.png"
                )
            )

        self.load_deadlines()

        self.main_layout = FloatLayout()

        self.show_main_interface()

        Clock.schedule_interval(
            self.update_countdowns,
            1
        )

        return self.main_layout

    def load_deadlines(self):
        if not os.path.exists(self.save_path):
            self.deadlines = []
            return

        try:
            with open(
                self.save_path,
                "r",
                encoding="utf-8"
            ) as file:
                self.deadlines = json.load(file)

            if not isinstance(self.deadlines, list):
                self.deadlines = []

        except:
            self.deadlines = []

    def save_deadlines(self):
        try:
            with open(
                self.save_path,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    self.deadlines,
                    file,
                    indent=4
                )
        except:
            pass

    def clear_layout(self):
        if self.main_layout is not None:
            self.main_layout.clear_widgets()

    def show_main_interface(self):
        self.clear_layout()

        root = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1)
        )

        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(10)
        )

        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(5),
            padding=[dp(40), dp(20), dp(40), dp(30)]
        )

        content.bind(
            minimum_height=content.setter("height")
        )

        title = Label(
            text="DEADLINE MANAGER",
            font_size=dp(30),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(55)
        )

        content.add_widget(title)

        self.search_entry = TextInput(
            hint_text="Search deadlines...",
            font_size=dp(14),
            multiline=False,
            size_hint_y=None,
            height=dp(45),
            size_hint_x=None,
            width=dp(400),
            pos_hint={"center_x": 0.5},
            background_color=(0.09, 0.09, 0.09, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            padding=[dp(12), dp(10)]
        )

        self.search_entry.bind(
            text=self.refresh_deadlines
        )

        content.add_widget(self.search_entry)

        counter_box = StripeCounter(
            size_hint_y=None,
            height=dp(100),
            size_hint_x=None,
            width=dp(500),
            pos_hint={"center_x": 0.5}
        )

        self.counter_label = Label(
            text=f"TOTAL DEADLINES: {len(self.deadlines)}",
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 1)
        )

        counter_box.add_widget(
            self.counter_label
        )

        content.add_widget(counter_box)

        self.form_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(0),
            opacity=0,
            spacing=dp(5)
        )

        self.name_entry = self.create_input(
            "Deadline Name"
        )

        self.day_entry = self.create_input(
            "Day"
        )

        self.month_entry = self.create_input(
            "Month"
        )

        self.year_entry = self.create_input(
            "Year"
        )

        self.form_layout.add_widget(
            self.name_entry
        )

        self.form_layout.add_widget(
            self.day_entry
        )

        self.form_layout.add_widget(
            self.month_entry
        )

        self.form_layout.add_widget(
            self.year_entry
        )

        self.result_label = Label(
            text="",
            color=(1, 0.65, 0, 1),
            font_size=dp(13),
            size_hint_y=None,
            height=dp(35)
        )

        self.form_layout.add_widget(
            self.result_label
        )

        create_button = Button(
            text="CREATE DEADLINE",
            font_size=dp(13),
            bold=True,
            color=(1, 1, 1, 1),
            background_normal="",
            background_color=(0.20, 0.20, 0.20, 1),
            size_hint_y=None,
            height=dp(42)
        )

        create_button.bind(
            on_release=lambda instance:
            self.add_deadline()
        )

        self.form_layout.add_widget(
            create_button
        )

        content.add_widget(
            self.form_layout
        )

        self.add_button = Button(
            text="ADD DEADLINE",
            font_size=dp(14),
            bold=True,
            color=(1, 1, 1, 1),
            background_normal="",
            background_color=(0.13, 0.13, 0.13, 1),
            size_hint_y=None,
            height=dp(50),
            size_hint_x=None,
            width=dp(250),
            pos_hint={"center_x": 0.5}
        )

        self.add_button.bind(
            on_release=lambda instance:
            self.show_add_form()
        )

        content.add_widget(
            self.add_button
        )

        self.back_button = Button(
            text="BACK",
            font_size=dp(13),
            bold=True,
            color=(1, 1, 1, 1),
            background_normal="",
            background_color=(0.13, 0.13, 0.13, 1),
            size_hint_y=None,
            height=dp(42),
            size_hint_x=None,
            width=dp(200),
            pos_hint={"center_x": 0.5},
            opacity=0,
            disabled=True
        )

        self.back_button.bind(
            on_release=lambda instance:
            self.hide_add_form()
        )

        content.add_widget(
            self.back_button
        )

        heading = Label(
            text="YOUR DEADLINES",
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(50)
        )

        content.add_widget(heading)

        self.deadline_display = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(7)
        )

        self.deadline_display.bind(
            minimum_height=
            self.deadline_display.setter("height")
        )

        content.add_widget(
            self.deadline_display
        )

        scroll.add_widget(content)

        root.add_widget(scroll)

        self.main_layout.add_widget(root)

        self.refresh_deadlines()

    def create_input(self, label_text):
        layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(70)
        )

        label = Label(
            text=label_text,
            font_size=dp(14),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(25)
        )

        entry = TextInput(
            font_size=dp(14),
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            background_color=(0.09, 0.09, 0.09, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            padding=[dp(10), dp(8)]
        )

        layout.add_widget(label)
        layout.add_widget(entry)

        return layout

    def get_entry(self, layout):
        return layout.children[0]

    def show_add_form(self):
        self.add_button.opacity = 0
        self.add_button.disabled = True

        self.form_layout.height = dp(395)
        self.form_layout.opacity = 1

        self.back_button.opacity = 1
        self.back_button.disabled = False

    def hide_add_form(self):
        self.form_layout.height = dp(0)
        self.form_layout.opacity = 0

        self.add_button.opacity = 1
        self.add_button.disabled = False

        self.back_button.opacity = 0
        self.back_button.disabled = True

        self.name_entry.children[0].text = ""
        self.day_entry.children[0].text = ""
        self.month_entry.children[0].text = ""
        self.year_entry.children[0].text = ""

        self.result_label.text = ""

    def add_deadline(self):
        name = self.name_entry.children[0].text.strip()
        day = self.day_entry.children[0].text.strip()
        month = self.month_entry.children[0].text.strip()
        year = self.year_entry.children[0].text.strip()

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
                1, 0.65, 0, 1
            )
            return

        try:
            deadline_date = datetime(
                int(year),
                int(month),
                int(day)
            )

            if (
                deadline_date.date()
                < datetime.now().date()
            ):
                self.result_label.text = (
                    "Please enter a valid date."
                )
                self.result_label.color = (
                    1, 0.65, 0, 1
                )
                return

            formatted_date = (
                deadline_date.strftime(
                    "%d/%m/%Y"
                )
            )

        except ValueError:
            self.result_label.text = (
                "Please enter a valid date."
            )
            self.result_label.color = (
                1, 0.65, 0, 1
            )
            return

        for existing in self.deadlines:
            if (
                existing["name"].casefold()
                == name.casefold()
                and existing["date"]
                == formatted_date
            ):
                self.result_label.text = (
                    "You have already created this deadline."
                )
                self.result_label.color = (
                    1, 0, 0, 1
                )
                return

        self.deadlines.append({
            "name": name,
            "date": formatted_date,
            "pinned": False
        })

        self.save_deadlines()

        self.result_label.text = (
            "Deadline created successfully."
        )

        self.result_label.color = (
            0, 1, 0, 1
        )

        self.name_entry.children[0].text = ""
        self.day_entry.children[0].text = ""
        self.month_entry.children[0].text = ""
        self.year_entry.children[0].text = ""

        self.refresh_deadlines()

    def pinned_deadlines(self):
        for deadline in self.deadlines:
            if "pinned" not in deadline:
                deadline["pinned"] = False

        self.deadlines.sort(
            key=lambda deadline:
            deadline["pinned"],
            reverse=True
        )

    def toggle_pin(self, deadline):
        deadline["pinned"] = not deadline.get(
            "pinned",
            False
        )

        self.save_deadlines()
        self.refresh_deadlines()

    def delete_deadline(self, deadline):
        if deadline in self.deadlines:
            self.deadlines.remove(deadline)

        self.save_deadlines()
        self.refresh_deadlines()

    def get_time_left(self, deadline_date):
        now = datetime.now()

        deadline_end = datetime(
            deadline_date.year,
            deadline_date.month,
            deadline_date.day,
            23,
            59,
            59
        )

        difference = deadline_end - now

        total_seconds = int(
            difference.total_seconds()
        )

        if total_seconds <= 0:
            return "0d 0h 0 mins 0s"

        days = total_seconds // 86400
        remaining = total_seconds % 86400

        hours = remaining // 3600
        remaining %= 3600

        minutes = remaining // 60
        seconds = remaining % 60

        return (
            f"{days}d "
            f"{hours}h "
            f"{minutes} mins "
            f"{seconds}s"
        )

    def deadline_status(self, deadline):
        try:
            deadline_date = datetime.strptime(
                deadline["date"],
                "%d/%m/%Y"
            )
        except:
            return (
                "Please enter a valid date.",
                (1, 0.65, 0, 1)
            )

        today = datetime.now().date()

        difference = (
            deadline_date.date() - today
        ).days

        pin_text = (
            "\nPinned 📌"
            if deadline.get("pinned", False)
            else "\nNot pinned"
        )

        if difference < 0:
            days_ago = abs(difference)

            if days_ago == 1:
                time_text = "1 day ago"
            else:
                time_text = (
                    f"{days_ago} days ago"
                )

            return (
                "OVERDUE"
                f"\nDeadline finished {time_text}."
                f"{pin_text}",
                (1, 0, 0, 1)
            )

        if difference == 2:
            return (
                "⚠ Deadline is near!"
                f"\nTime left : "
                f"{self.get_time_left(deadline_date)}"
                f"{pin_text}",
                (1, 0.55, 0, 1)
            )

        if difference == 1:
            return (
                "Deadline is near!"
                f"\nTime left : "
                f"{self.get_time_left(deadline_date)}"
                f"{pin_text}",
                (1, 0.65, 0, 1)
            )

        if difference == 0:
            return (
                "⚠ Today is last date!"
                f"\nTime left : "
                f"{self.get_time_left(deadline_date)}"
                f"{pin_text}",
                (1, 0, 0, 1)
            )

        return (
            "Deadline is not near."
            f"\nTime left : "
            f"{self.get_time_left(deadline_date)}"
            f"{pin_text}",
            (0, 1, 0, 1)
        )

    def refresh_deadlines(self, *args):
        if self.deadline_display is None:
            return

        self.deadline_display.clear_widgets()

        self.pinned_deadlines()

        search_text = ""

        if self.search_entry is not None:
            search_text = (
                self.search_entry.text.strip().casefold()
            )

        if search_text == "search deadlines...":
            search_text = ""

        for deadline in self.deadlines:
            name = deadline["name"]
            date = deadline["date"]

            if (
                search_text not in name.casefold()
                and search_text not in date.casefold()
            ):
                continue

            status_text, status_color = (
                self.deadline_status(deadline)
            )

            card = DeadlineCard(
                deadline=deadline,
                status_text=status_text,
                status_color=status_color,
                pin_callback=self.toggle_pin,
                delete_callback=self.delete_deadline
            )

            self.deadline_display.add_widget(
                card
            )

        if self.counter_label is not None:
            self.counter_label.text = (
                f"TOTAL DEADLINES: "
                f"{len(self.deadlines)}"
            )

    def play_sound(self):
        if not os.path.exists(
            self.sound_path
        ):
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(
                self.sound_path
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

            key = (
                deadline["name"]
                + "|"
                + deadline["date"]
            )

            if difference == 1:
                sound_key = "sound|" + key

                if sound_key not in self.sound_played:
                    self.sound_played.add(
                        sound_key
                    )
                    self.play_sound()

                notification_key = (
                    "tomorrow|" + key
                )

                if (
                    notification_key
                    not in self.notification_sent
                ):
                    self.notification_sent.add(
                        notification_key
                    )

                    self.send_notification(
                        "Life System Manager",
                        "Hello from Life System Manager. "
                        f"The deadline ({deadline['name']}) "
                        "is scheduled to conclude tomorrow."
                    )

            elif difference == 0:
                notification_key = (
                    "today|" + key
                )

                if (
                    notification_key
                    not in self.notification_sent
                ):
                    self.notification_sent.add(
                        notification_key
                    )

                    self.send_notification(
                        "Life System Manager",
                        "Hello from Life System Manager. "
                        f"The deadline ({deadline['name']}) "
                        "is due today. We hope you "
                        "have completed the deadline."
                    )

    def update_countdowns(self, dt):
        self.check_deadline_alerts()
        self.refresh_deadlines()


if __name__ == "__main__":
    DeadlineManager().run()
