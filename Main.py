import os
import json
import pygame
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from plyer import notification


Window.size = (900, 600)
Window.minimum_width = 900
Window.minimum_height = 600
Window.maximum_width = 900
Window.maximum_height = 600
Window.clearcolor = (0, 0, 0, 1)


class StripeCounter(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(0.067, 0.067, 0.067, 1)
            Color(0.145, 0.145, 0.145, 1)

            self.stripes = []

            for x in range(-100, 600, 25):
                self.stripes.append(
                    Line(
                        points=(x, 0, x + 100, 100),
                        width=1
                    )
                )

    def on_size(self, *args):
        self.draw_stripes()

    def on_pos(self, *args):
        self.draw_stripes()

    def draw_stripes(self):
        for i, line in enumerate(self.stripes):
            x = self.x - 100 + i * 25

            line.points = (
                x,
                self.y,
                x + 100,
                self.y + self.height
            )


class DeadlineManager(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.deadlines = []

        self.main_layout = None
        self.content = None
        self.deadline_display = None
        self.counter_label = None
        self.search_entry = None

        self.form_area = None
        self.form_frame = None
        self.add_holder = None
        self.add_button = None
        self.back_button = None
        self.result_label = None

        self.name_entry = None
        self.day_entry = None
        self.month_entry = None
        self.year_entry = None

        self.main_scroll = None

        self.intro_image = None
        self.intro_opacity = 0

        self.countdown_event = None

        self.sound_played = set()
        self.notification_sent = set()

        self.card_delete_buttons = {}

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

        self.icon_path = os.path.join(
            self.base_path,
            "Icon.png"
        )

    def build(self):
        if os.path.exists(self.icon_path):
            Window.set_icon(self.icon_path)

        self.load_deadlines()

        self.main_layout = Widget()

        Clock.schedule_once(
            self.intro_animation,
            0
        )

        return self.main_layout

    def load_deadlines(self):
        if not os.path.exists(self.save_path):
            self.deadlines = []
            return

        try:
            with open(
                self.save_path,
                "r"
            ) as file:
                self.deadlines = json.load(file)

        except:
            self.deadlines = []

        for deadline in self.deadlines:
            if "pinned" not in deadline:
                deadline["pinned"] = False

    def save_deadlines(self):
        try:
            with open(
                self.save_path,
                "w"
            ) as file:
                json.dump(
                    self.deadlines,
                    file,
                    indent=4
                )
        except:
            pass

    def clear_root(self):
        if self.main_layout is not None:
            self.main_layout.clear_widgets()

    def intro_animation(self, *args):
        self.clear_root()

        layout = AnchorLayout(
            anchor_x="center",
            anchor_y="center"
        )

        self.intro_image = Image(
            source=self.icon_path,
            size_hint=(None, None),
            size=(dp(350), dp(350)),
            opacity=0
        )

        layout.add_widget(
            self.intro_image
        )

        self.main_layout.add_widget(
            layout
        )

        self.intro_opacity = 0

        Clock.schedule_interval(
            self.fade_in,
            1 / 40
        )

    def fade_in(self, dt):
        self.intro_opacity += 0.05

        if self.intro_opacity >= 1:
            self.intro_opacity = 1
            self.intro_image.opacity = 1

            Clock.unschedule(
                self.fade_in
            )

            Clock.schedule_once(
                self.start_fade_out,
                0.7
            )

        else:
            self.intro_image.opacity = (
                self.intro_opacity
            )

    def start_fade_out(self, dt):
        self.intro_opacity = 1

        Clock.schedule_interval(
            self.fade_out,
            1 / 40
        )

    def fade_out(self, dt):
        self.intro_opacity -= 0.05

        if self.intro_opacity <= 0:
            self.intro_opacity = 0
            self.intro_image.opacity = 0

            Clock.unschedule(
                self.fade_out
            )

            self.show_main_interface()

        else:
            self.intro_image.opacity = (
                self.intro_opacity
            )

    def hex_color(self, value):
        value = value.replace(
            "#",
            ""
        )

        return (
            int(value[0:2], 16) / 255,
            int(value[2:4], 16) / 255,
            int(value[4:6], 16) / 255,
            1
        )

    def make_button(
        self,
        text,
        font_size=14,
        bg="#222222",
        height=45
    ):
        return Button(
            text=text,
            font_size=font_size,
            bold=True,
            color=(1, 1, 1, 1),
            background_normal="",
            background_color=self.hex_color(bg),
            size_hint_y=None,
            height=dp(height)
        )

    def show_main_interface(self):
        self.clear_root()

        root_layout = BoxLayout(
            orientation="horizontal"
        )

        self.main_scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(8),
            scroll_type=[
                "bars",
                "content"
            ]
        )

        self.content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(5),
            padding=(
                dp(40),
                dp(20),
                dp(40),
                dp(20)
            )
        )

        self.content.bind(
            minimum_height=
            self.content.setter("height")
        )

        title = Label(
            text="DEADLINE MANAGER",
            font_size=30,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(55)
        )

        self.content.add_widget(
            title
        )

        self.search_entry = TextInput(
            text="Search deadlines...",
            font_size=14,
            multiline=False,
            size_hint=(None, None),
            width=dp(400),
            height=dp(42),
            background_color=
            self.hex_color("#171717"),
            foreground_color=
            (1, 1, 1, 1),
            cursor_color=
            (1, 1, 1, 1),
            padding=(
                dp(12),
                dp(10)
            )
        )

        self.search_entry.bind(
            focus=self.search_focus
        )

        self.search_entry.bind(
            text=self.search_changed
        )

        search_holder = AnchorLayout(
            anchor_x="center",
            size_hint_y=None,
            height=dp(62)
        )

        search_holder.add_widget(
            self.search_entry
        )

        self.content.add_widget(
            search_holder
        )

        counter_holder = AnchorLayout(
            anchor_x="center",
            size_hint_y=None,
            height=dp(100)
        )

        counter_box = StripeCounter(
            size_hint=(None, None),
            size=(
                dp(500),
                dp(100)
            )
        )

        self.counter_label = Label(
            text="TOTAL DEADLINES: 0",
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1)
        )

        counter_box.add_widget(
            self.counter_label
        )

        counter_holder.add_widget(
            counter_box
        )

        self.content.add_widget(
            counter_holder
        )

        self.form_area = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(5)
        )

        self.add_holder = AnchorLayout(
            anchor_x="center",
            size_hint_y=None,
            height=dp(70)
        )

        self.add_button = self.make_button(
            "ADD DEADLINE",
            14,
            "#222222",
            50
        )

        self.add_button.size_hint_x = None
        self.add_button.width = dp(230)

        self.add_button.bind(
            on_release=self.show_add_form
        )

        self.add_holder.add_widget(
            self.add_button
        )

        self.form_area.add_widget(
            self.add_holder
        )

        self.form_frame = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(3),
            padding=(
                0,
                dp(5)
            )
        )

        self.form_frame.bind(
            minimum_height=
            self.form_frame.setter("height")
        )

        self.form_frame.height = 0

        self.add_form_field(
            "Deadline Name",
            "name"
        )

        self.add_form_field(
            "Day",
            "day"
        )

        self.add_form_field(
            "Month",
            "month"
        )

        self.add_form_field(
            "Year",
            "year"
        )

        self.result_label = Label(
            text="",
            font_size=13,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(30)
        )

        self.form_frame.add_widget(
            self.result_label
        )

        create_button = self.make_button(
            "CREATE DEADLINE",
            13,
            "#333333",
            44
        )

        create_button.bind(
            on_release=self.add_deadline
        )

        self.form_frame.add_widget(
            create_button
        )

        back_holder = AnchorLayout(
            anchor_x="center",
            size_hint_y=None,
            height=dp(45)
        )

        self.back_button = self.make_button(
            "BACK",
            13,
            "#222222",
            42
        )

        self.back_button.size_hint_x = None
        self.back_button.width = dp(160)

        self.back_button.bind(
            on_release=self.hide_add_form
        )

        back_holder.add_widget(
            self.back_button
        )

        self.form_frame.add_widget(
            back_holder
        )

        self.form_area.add_widget(
            self.form_frame
        )

        self.content.add_widget(
            self.form_area
        )

        heading = Label(
            text="YOUR DEADLINES",
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(55)
        )

        self.content.add_widget(
            heading
        )

        self.deadline_display = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(7)
        )

        self.deadline_display.bind(
            minimum_height=
            self.deadline_display.setter("height")
        )

        self.content.add_widget(
            self.deadline_display
        )

        self.main_scroll.add_widget(
            self.content
        )

        root_layout.add_widget(
            self.main_scroll
        )

        self.main_layout.add_widget(
            root_layout
        )

        self.refresh_deadlines()

        if self.countdown_event is not None:
            Clock.unschedule(
                self.countdown_event
            )

        self.countdown_event = (
            Clock.schedule_interval(
                self.update_countdowns,
                1
            )
        )

        self.check_deadline_alerts()

    def add_form_field(
        self,
        label_text,
        field_name
    ):
        label = Label(
            text=label_text,
            font_size=14,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(30)
        )

        self.form_frame.add_widget(
            label
        )

        entry = TextInput(
            font_size=14,
            multiline=False,
            size_hint=(None, None),
            width=dp(360),
            height=dp(40),
            background_color=
            self.hex_color("#171717"),
            foreground_color=
            (1, 1, 1, 1),
            cursor_color=
            (1, 1, 1, 1),
            padding=(
                dp(10),
                dp(8)
            )
        )

        holder = AnchorLayout(
            anchor_x="center",
            size_hint_y=None,
            height=dp(48)
        )

        holder.add_widget(
            entry
        )

        self.form_frame.add_widget(
            holder
        )

        setattr(
            self,
            field_name + "_entry",
            entry
        )

    def search_focus(
        self,
        instance,
        focused
    ):
        if focused:
            if instance.text == "Search deadlines...":
                instance.text = ""

        else:
            if instance.text == "":
                instance.text = (
                    "Search deadlines..."
                )

    def search_changed(
        self,
        instance,
        value
    ):
        if self.deadline_display is not None:
            self.refresh_deadlines()

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

    def get_time_left(
        self,
        deadline_datetime
    ):
        now = datetime.now()

        end = deadline_datetime.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=0
        )

        remaining = end - now

        if remaining.total_seconds() <= 0:
            return "0s"

        total_seconds = int(
            remaining.total_seconds()
        )

        days, remainder = divmod(
            total_seconds,
            86400
        )

        hours, remainder = divmod(
            remainder,
            3600
        )

        minutes, seconds = divmod(
            remainder,
            60
        )

        parts = []

        if days:
            parts.append(
                f"{days}d"
            )

        if hours or days:
            parts.append(
                f"{hours}h"
            )

        if minutes or hours or days:
            parts.append(
                f"{minutes} mins"
            )

        parts.append(
            f"{seconds}s"
        )

        return " ".join(parts)

    def deadline_status(
        self,
        deadline_date,
        deadline
    ):
        today = datetime.now().date()

        deadline_day = (
            deadline_date.date()
        )

        difference = (
            deadline_day - today
        ).days

        pinned_text = (
            "\nPinned 📌"
            if deadline.get(
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
                text = "1 day ago"
            else:
                text = (
                    f"{days_ago} days ago"
                )

            return (
                "OVERDUE"
                f"\nDeadline finished {text}."
                f"{pinned_text}",
                "red"
            )

        if difference == 0:
            return (
                "⚠ Today is last date!"
                f"{pinned_text}",
                "red"
            )

        if difference == 2:
            return (
                "⚠ Deadline is near!"
                f"\nTime left : "
                f"{self.get_time_left(deadline_date)}"
                f"{pinned_text}",
                "orange"
            )

        if difference == 1:
            return (
                "⚠ Deadline is tomorrow!"
                f"\nTime left : "
                f"{self.get_time_left(deadline_date)}"
                f"{pinned_text}",
                "orange"
            )

        return (
            "Deadline is not near."
            f"\nTime left : "
            f"{self.get_time_left(deadline_date)}"
            f"{pinned_text}",
            "lime"
        )

    def play_sound(self):
        if not os.path.exists(
            self.sound_path
        ):
            return

        try:
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
                sound_key = (
                    "sound|"
                    + key
                )

                notification_key = (
                    "tomorrow|"
                    + key
                )

                if sound_key not in self.sound_played:
                    self.sound_played.add(
                        sound_key
                    )

                    self.play_sound()

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
                    "today|"
                    + key
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

    def refresh_deadlines(
        self,
        *args
    ):
        if self.deadline_display is None:
            return

        self.pinned_deadlines()

        self.deadline_display.clear_widgets()

        self.card_delete_buttons.clear()

        search_text = (
            self.search_entry.text.lower()
        )

        if search_text == (
            "search deadlines..."
        ):
            search_text = ""

        for deadline in self.deadlines:
            name = deadline["name"]
            date = deadline["date"]

            if (
                search_text not in name.lower()
                and search_text not in date.lower()
            ):
                continue

            try:
                deadline_datetime = (
                    datetime.strptime(
                        date,
                        "%d/%m/%Y"
                    )
                )

            except:
                continue

            status_text, status_color = (
                self.deadline_status(
                    deadline_datetime,
                    deadline
                )
            )

            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(165),
                padding=(
                    dp(15),
                    dp(10)
                ),
                spacing=dp(2)
            )

            with card.canvas.before:
                Color(
                    0.09,
                    0.09,
                    0.09,
                    1
                )

            name_label = Label(
                text=name,
                font_size=16,
                bold=True,
                color=(1, 1, 1, 1),
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(32)
            )

            date_label = Label(
                text=f"Date: {date}",
                font_size=12,
                color=(
                    0.667,
                    0.667,
                    0.667,
                    1
                ),
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(25)
            )

            if status_color == "red":
                color = (
                    1,
                    0,
                    0,
                    1
                )

            elif status_color == "orange":
                color = (
                    1,
                    0.55,
                    0,
                    1
                )

            else:
                color = (
                    0,
                    1,
                    0,
                    1
                )

            status_label = Label(
                text=status_text,
                font_size=12,
                bold=True,
                color=color,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(55)
            )

            pin_button = self.make_button(
                (
                    "UNPIN"
                    if deadline.get(
                        "pinned",
                        False
                    )
                    else "PIN"
                ),
                10,
                (
                    "#806000"
                    if deadline.get(
                        "pinned",
                        False
                    )
                    else "#333333"
                ),
                36
            )

            pin_button.bind(
                on_release=lambda instance,
                d=deadline:
                self.toggle_pin(d)
            )

            delete_button = self.make_button(
                "DELETE DEADLINE",
                11,
                "#661111",
                38
            )

            delete_button.bind(
                on_release=lambda instance,
                d=deadline:
                self.delete_deadline(d)
            )

            delete_button.opacity = 0
            delete_button.disabled = True

            card.add_widget(
                name_label
            )

            card.add_widget(
                date_label
            )

            card.add_widget(
                status_label
            )

            card.add_widget(
                pin_button
            )

            card.add_widget(
                delete_button
            )

            self.card_delete_buttons[
                id(card)
            ] = delete_button

            def card_touch(
                instance,
                touch,
                c=card
            ):
                if c.collide_point(
                    *touch.pos
                ):
                    self.toggle_delete(
                        c
                    )

                return False

            card.bind(
                on_touch_down=card_touch
            )

            self.deadline_display.add_widget(
                card
            )

        self.counter_label.text = (
            f"TOTAL DEADLINES: "
            f"{len(self.deadlines)}"
        )

    def toggle_delete(
        self,
        card
    ):
        delete_button = (
            self.card_delete_buttons.get(
                id(card)
            )
        )

        if delete_button is None:
            return

        if delete_button.opacity == 0:
            delete_button.opacity = 1
            delete_button.disabled = False
            card.height = dp(205)

        else:
            delete_button.opacity = 0
            delete_button.disabled = True
            card.height = dp(165)

    def delete_deadline(
        self,
        deadline
    ):
        if deadline in self.deadlines:
            self.deadlines.remove(
                deadline
            )

            self.save_deadlines()

            self.refresh_deadlines()

    def toggle_pin(
        self,
        deadline
    ):
        deadline["pinned"] = not deadline.get(
            "pinned",
            False
        )

        self.save_deadlines()

        self.refresh_deadlines()

    def show_add_form(
        self,
        instance
    ):
        if self.add_button.parent is not None:
            self.add_button.parent.remove_widget(
                self.add_button
            )

        self.form_frame.height = dp(390)

    def hide_add_form(
        self,
        instance
    ):
        self.form_frame.height = 0

        if self.add_button.parent is None:
            self.add_holder.add_widget(
                self.add_button
            )

        self.result_label.text = ""

        self.name_entry.text = ""
        self.day_entry.text = ""
        self.month_entry.text = ""
        self.year_entry.text = ""

    def add_deadline(
        self,
        instance
    ):
        name = (
            self.name_entry.text.strip()
        )

        day = (
            self.day_entry.text.strip()
        )

        month = (
            self.month_entry.text.strip()
        )

        year = (
            self.year_entry.text.strip()
        )

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

        except ValueError:
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

        for existing in self.deadlines:
            if (
                existing["name"].casefold()
                == name.casefold()
                and existing["date"]
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

        self.result_label.text = (
            "Deadline created successfully."
        )

        self.result_label.color = (
            0,
            1,
            0,
            1
        )

        self.name_entry.text = ""
        self.day_entry.text = ""
        self.month_entry.text = ""
        self.year_entry.text = ""

        self.refresh_deadlines()

        self.check_deadline_alerts()

    def update_countdowns(
        self,
        dt
    ):
        if self.deadline_display is None:
            return

        self.check_deadline_alerts()

        self.refresh_deadlines()


if __name__ == "__main__":
    DeadlineManager().run()
