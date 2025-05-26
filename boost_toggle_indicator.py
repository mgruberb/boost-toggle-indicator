#!/usr/bin/env python3

#
# boost_toggle_indicator.py - CPU Boost toggle utility
#
# Copyright (C) 2025 mgruberb
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import gi
import subprocess
import os
from pathlib import Path

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import Gtk, GLib, AyatanaAppIndicator3 as AppIndicator3

BOOST_FILE = Path("/sys/devices/system/cpu/cpufreq/boost")


if not BOOST_FILE.exists():
    print("Boost control not available on this CPU.")
    sys.exit(1)

config_dir = Path.home() / ".config" / "boost-toggle"
config_dir.mkdir(parents=True, exist_ok=True)

CUSTOM_ON_ICON_PATH = "icons/boost-on.svg"
CUSTOM_OFF_ICON_PATH = "icons/boost-off.svg"
FALLBACK_ICON_NAME = "cpu"

STATE_FILE = config_dir / "state"

class BoostToggleApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.mgruberb.BoostToggle")
        self.window = None
        self.indicator = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        # create Ayatana appindicator (tray icon)
        state = self.load_saved_state()
        self.indicator = AppIndicator3.Indicator.new(
            "boost-toggle-indicator",
            str(self.get_icon(state)),
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # create the menu
        menu = Gtk.Menu()

        self.toggle_item = Gtk.CheckMenuItem(label="Enable CPU Boost")
        self.toggle_item.set_active(self.get_boost_status())
        self.toggle_item.connect("toggled", self.on_toggle)
        menu.append(self.toggle_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", lambda _: self.quit())
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

    def get_icon(self, state):
        suffix = CUSTOM_ON_ICON_PATH if state else CUSTOM_OFF_ICON_PATH
        for test_path in [Path.cwd() / suffix, Path.home() / ".local" / "share" / "boost-toggle" / suffix, Path("/usr/share/boost-toggle") / suffix]:
            if os.path.exists(test_path):
                #print(f"Found path: {test_path}") 
                return str(test_path)  # use local dir absolute path
            #else:
            	#print(f"Could not find path: {test_path}") 
        return FALLBACK_ICON_NAME

    def update_icon(self):
        state = self.get_boost_status()
        icon = self.get_icon(state)
        description = "CPU boost " + "enabled" if state else "disabled"
        self.indicator.set_icon_full(icon, description)

    def do_activate(self):
        if not self.window:
            self.window = Gtk.ApplicationWindow(application=self)
            self.window.set_title("CPU Boost Toggle")
            self.window.set_default_size(200, 100)

            label = Gtk.Label(label="CPU Boost Toggle running in tray.\nUse the tray icon to toggle.")
            label.set_justify(Gtk.Justification.CENTER)

            self.window.add(label)
            #self.window.show_all()  # disable window presentation - no app window necessary
        #self.window.present()       # disable window presentation - no app window necessary 
        pass

    def get_boost_status(self):
        try:
            return BOOST_FILE.read_text().strip() == "1"
        except Exception as e:
            print(f"Failed to read boost status: {e}")
            return False

    def set_boost(self, enable):
        value = "1" if enable else "0"
        try:
            subprocess.run(
                ["pkexec", "tee", str(BOOST_FILE)],
                input=value.encode(),
                check=True
            )
        except Exception as e:
            print(f"Failed to set boost: {e}")

    def on_toggle(self, menu_item):
        state = menu_item.get_active()        
        self.set_boost(state)
        self.update_icon()
        self.save_state(state)
    
    def load_saved_state(self):
        try:
            return STATE_FILE.read_text().strip() == "1"
        except Exception:
            return True # default to boost = ON
    
    def save_state(self, enabled):
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text("1\n" if enabled else "0\n")
        except Exception as e:
            printf(f"Failed to save state: {e}")
            
app = BoostToggleApp()
app.run()

