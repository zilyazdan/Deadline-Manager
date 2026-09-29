import os
import sys
import json
import pygame

from datetime import datetime, date

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

try:
    from plyer import notification
except Exception:
    notification = None


Window.clearcolor = (0, 0, 0, 1)
Window.size = (900, 600)
Window.minimum_width = 500
Window.minimum_height = 500


def get_data_folder():
    if getattr(sys, "frozen", False):
        folder = os.path.join(os.path.dirname(sys.executable), "LifeSystemManager")
    else:
        folder = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(folder, exist_ok=True)
    return folder


DATA_FOLDER = get_data_folder()
DATA_FILE = os.path.join(DATA_FOLDER, "deadlines.json")
ALARM_FILE = os.path.join(DATA_FOLDER, "Alarm Sound Effect.mp3")


def resource_path(filename):
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base, filename)


class DeadlineCard(BoxLayout):
    def __init__(self, manager, deadline, **kwargs):
        super().__init__(**kwargs)

        self.manager = manager
        self.deadline = deadline

        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(150)
        self.padding = dp(15)
        self.spacing = dp(5)

        with self.canvas.before:
            Color(0.06, 0.06, 0.06, 1)
            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)]
            )

            Color(0.2, 0.2, 0.2, 1)
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
            pos=self.update_background,
            size=self.update_background
        )

        name = str(deadline.get("name", "Unnamed Deadline"))

        day = str(deadline.get("day", ""))
        month = str(deadline.get("month", ""))
        year = str(deadline.get("year", ""))

        try:
            deadline_date = date(
                int(year),
                int(month),
                int(day)
            )

            today = date.today()
            difference = (deadline_date - today).days

        except Exception:
            difference = 0

        if difference < 0:
            days_ago = abs(difference)

            if days_ago == 1:
                status = "Deadline finished 1 day ago."
            else:
                status = f"Deadline finished {days_ago} days ago."

            status_color = (1, 0.25, 0.25, 1)

        elif difference == 0:
            status = "OVERDUE"
            status_color = (1, 0.2, 0.2, 1)

        elif difference == 1:
            status = "Deadline is tomorrow."
            status_color = (1, 0.7, 0.2, 1)

        elif difference == 2:
            status = "⚠ Deadline is near!"
            status_color = (1, 0.8, 0.2, 1)

        else:
            status = f"Days Remaining : {difference}"
            status_color = (0.3, 1, 0.3, 1)

        title = Label(
            text=name,
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(35)
        )

        title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        date_label = Label(
            text=f"{day}/{month}/{year}",
            font_size=16,
            color=(0.75, 0.75, 0.75, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(30)
        )

        date_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        status_label = Label(
            text=status,
            font_size=16,
            bold=True,
            color=status_color,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(30)
        )

        status_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        buttons = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(35)
        )

        pinned = deadline.get("pinned", False)

        pin_button = Button(
            text="UNPIN" if pinned else "PIN",
            font_size=14
        )

        delete_button = Button(
            text="DELETE",
            font_size=14
        )

        pin_button.bind(
            on_release=lambda instance:
            self.toggle_pin()
        )

        delete_button.bind(
            on_release=lambda instance:
            self.delete_deadline()
        )

        buttons.add_widget(pin_button)
        buttons.add_widget(delete_button)

        self.add_widget(title)
        self.add_widget(date_label)
        self.add_widget(status_label)
        self.add_widget(buttons)

    def update_background(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size

        self.border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(12)
        )

    def toggle_pin(self):
        self.deadline["pinned"] = not self.deadline.get("pinned", False)

        self.manager.save_deadlines()
        self.manager.refresh_deadlines()

    def delete_deadline(self):
        if self.deadline in self.manager.deadlines:
            self.manager.deadlines.remove(self.deadline)

        self.manager.save_deadlines()
        self.manager.refresh_deadlines()


class DeadlineManager(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.deadlines = []
        self.search_input = None
        self.deadline_layout = None
        self.main_page = None

        self.load_deadlines()

        try:
            pygame.mixer.init()
        except Exception:
            pass

    def build(self):
        self.show_main_interface()

        Clock.schedule_interval(
            self.check_deadlines,
            30
        )

        return self.main_page

    def load_deadlines(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                self.deadlines = json.load(file)

        except (FileNotFoundError, json.JSONDecodeError):
            self.deadlines = []

        for deadline in self.deadlines:
            if "pinned" not in deadline:
                deadline["pinned"] = False

            if "day" not in deadline or "month" not in deadline or "year" not in deadline:
                old_date = deadline.get("date", "")

                try:
                    parsed = datetime.strptime(
                        old_date,
                        "%d/%m/%Y"
                    )

                    deadline["day"] = parsed.day
                    deadline["month"] = parsed.month
                    deadline["year"] = parsed.year

                except Exception:
                    deadline["day"] = ""
                    deadline["month"] = ""
                    deadline["year"] = ""

    def save_deadlines(self):
        try:
            with open(
                DATA_FILE,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    self.deadlines,
                    file,
                    indent=4
                )

        except Exception:
            pass

    def show_main_interface(self):
        self.main_page = FloatLayout()

        page = BoxLayout(
            orientation="vertical",
            padding=[
                dp(30),
                dp(20),
                dp(30),
                dp(20)
            ],
            spacing=dp(10)
        )

        title = Label(
            text="DEADLINE MANAGER",
            font_size=30,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(55)
        )

        page.add_widget(title)

        self.search_input = TextInput(
            hint_text="Search deadlines...",
            multiline=False,
            font_size=17,
            size_hint_y=None,
            height=dp(45),
            padding=[
                dp(15),
                dp(10)
            ]
        )

        self.search_input.bind(
            text=lambda instance, value:
            self.refresh_deadlines()
        )

        page.add_widget(self.search_input)

        add_button = Button(
            text="ADD DEADLINE",
            font_size=17,
            bold=True,
            size_hint_y=None,
            height=dp(45)
        )

        add_button.bind(
            on_release=lambda instance:
            self.show_add_deadline()
        )

        page.add_widget(add_button)

        your_deadlines = Label(
            text="YOUR DEADLINES",
            font_size=22,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(45)
        )

        page.add_widget(your_deadlines)

        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True
        )

        self.deadline_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[
                0,
                dp(5),
                0,
                dp(10)
            ],
            size_hint_y=None
        )

        self.deadline_layout.bind(
            minimum_height=self.deadline_layout.setter(
                "height"
            )
        )

        scroll.add_widget(self.deadline_layout)

        page.add_widget(scroll)

        self.main_page.add_widget(page)

        self.refresh_deadlines()

    def refresh_deadlines(self):
        if not self.deadline_layout:
            return

        self.deadline_layout.clear_widgets()

        search_text = ""

        if self.search_input:
            search_text = (
                self.search_input.text
                .strip()
                .casefold()
            )

        filtered = []

        for deadline in self.deadlines:
            name = str(
                deadline.get("name", "")
            )

            day = str(
                deadline.get("day", "")
            )

            month = str(
                deadline.get("month", "")
            )

            year = str(
                deadline.get("year", "")
            )

            searchable = (
                name
                + " "
                + day
                + "/"
                + month
                + "/"
                + year
            ).casefold()

            if (
                not search_text
                or search_text in searchable
            ):
                filtered.append(deadline)

        filtered.sort(
            key=lambda item:
            not item.get("pinned", False)
        )

        if not filtered:
            no_deadlines = Label(
                text="No deadlines.",
                font_size=18,
                color=(0.7, 0.7, 0.7, 1),
                size_hint_y=None,
                height=dp(45)
            )

            self.deadline_layout.add_widget(
                no_deadlines
            )

        else:
            for deadline in filtered:
                card = DeadlineCard(
                    self,
                    deadline
                )

                self.deadline_layout.add_widget(
                    card
                )

    def show_add_deadline(self):
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(15)
        )

        name_input = TextInput(
            hint_text="Deadline name",
            multiline=False,
            font_size=16,
            size_hint_y=None,
            height=dp(45)
        )

        day_input = TextInput(
            hint_text="Day",
            multiline=False,
            input_filter="int",
            font_size=16,
            size_hint_y=None,
            height=dp(45)
        )

        month_input = TextInput(
            hint_text="Month",
            multiline=False,
            input_filter="int",
            font_size=16,
            size_hint_y=None,
            height=dp(45)
        )

        year_input = TextInput(
            hint_text="Year",
            multiline=False,
            input_filter="int",
            font_size=16,
            size_hint_y=None,
            height=dp(45)
        )

        buttons = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(45)
        )

        cancel_button = Button(
            text="CANCEL",
            font_size=15
        )

        add_button = Button(
            text="ADD",
            font_size=15
        )

        buttons.add_widget(cancel_button)
        buttons.add_widget(add_button)

        layout.add_widget(name_input)
        layout.add_widget(day_input)
        layout.add_widget(month_input)
        layout.add_widget(year_input)
        layout.add_widget(buttons)

        popup = Popup(
            title="ADD DEADLINE",
            content=layout,
            size_hint=(None, None),
            size=(dp(420), dp(400)),
            auto_dismiss=False
        )

        cancel_button.bind(
            on_release=popup.dismiss
        )

        def add_deadline(instance):
            name = name_input.text.strip()

            day_text = day_input.text.strip()
            month_text = month_input.text.strip()
            year_text = year_input.text.strip()

            if not name:
                self.show_message(
                    "Please enter a deadline name."
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

            except Exception:
                self.show_message(
                    "Please enter a valid date."
                )
                return

            if deadline_date < date.today():
                self.show_message(
                    "Please enter a valid date."
                )
                return

            for deadline in self.deadlines:
                old_name = str(
                    deadline.get("name", "")
                ).casefold()

                old_day = str(
                    deadline.get("day", "")
                )

                old_month = str(
                    deadline.get("month", "")
                )

                old_year = str(
                    deadline.get("year", "")
                )

                if (
                    old_name == name.casefold()
                    and old_day == str(day)
                    and old_month == str(month)
                    and old_year == str(year)
                ):
                    self.show_message(
                        "You have already created this deadline."
                    )
                    return

            new_deadline = {
                "name": name,
                "day": day,
                "month": month,
                "year": year,
                "date": deadline_date.strftime(
                    "%d/%m/%Y"
                ),
                "pinned": False
            }

            self.deadlines.append(
                new_deadline
            )

            self.save_deadlines()
            self.refresh_deadlines()

            popup.dismiss()

        add_button.bind(
            on_release=add_deadline
        )

        popup.open()

    def show_message(self, message):
        popup = Popup(
            title="DEADLINE MANAGER",
            content=Label(
                text=message,
                font_size=17
            ),
            size_hint=(None, None),
            size=(dp(400), dp(200))
        )

        popup.open()

    def check_deadlines(self, *args):
        today = date.today()

        for deadline in self.deadlines:
            try:
                deadline_date = date(
                    int(deadline["year"]),
                    int(deadline["month"]),
                    int(deadline["day"])
                )

            except Exception:
                continue

            if deadline_date == today:
                self.play_alarm()
                self.send_notification(
                    deadline.get(
                        "name",
                        "Deadline"
                    )
                )

    def play_alarm(self):
        try:
            sound_file = resource_path(
                "Alarm Sound Effect.mp3"
            )

            if not os.path.exists(sound_file):
                return

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(
                sound_file
            )

            pygame.mixer.music.play()

        except Exception:
            pass

    def send_notification(self, name):
        if notification is None:
            return

        try:
            notification.notify(
                title="Deadline Today",
                message=f"{name} is due today.",
                app_name="Deadline Manager",
                timeout=10
            )

        except Exception:
            pass

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if key == 27:
            return True

        return False

    def on_start(self):
        Window.bind(
            on_key_down=self.on_key_down
        )

    def on_stop(self):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass

        Window.unbind(
            on_key_down=self.on_key_down
        )


if __name__ == "__main__":
    DeadlineManager().run()
