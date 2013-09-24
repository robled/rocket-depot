#!/usr/bin/env python

import os
import re
import string
import subprocess
import time
import ConfigParser
from gi.repository import Gtk

de = os.environ.get('DESKTOP_SESSION')

if de == 'ubuntu' or de == 'ubuntu-2d':
    from gi.repository import Unity, Dbusmenu
    unity = True
else:
    unity = False

# Our config file
configfile = '%s/.rocket-depot' % os.environ['HOME']
config = ConfigParser.RawConfigParser()
config.read(configfile)

# Default options.  Overridden by config file.
options = {
    'host': 'host.example.com',
    # set the default RDP user to the local user by default
    'user': os.environ.get('USER', 'user'),
    'geometry': '1024x768',
    'program': 'rdesktop',
    'homeshare': 'false',
    'grabkeyboard': 'false',
    'fullscreen': 'false'
}

# Menu bar layout
UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='SaveCurrentConfig' />
      <menuitem action='SaveCurrentConfigAsDefault' />
      <menuitem action='DeleteCurrentConfig' />
      <menuitem action='FileQuit' />
    </menu>
    <menu action='Help'>
      <menuitem action='About'/>
    </menu>
  </menubar>
</ui>
"""


def write_config():
    with open(configfile, 'wb') as f:
        config.write(f)


# Write the config file
def save_config(section, window=None):
    # if the UI is running, let's see what's in the textboxes
    if window:
        window.grab_textboxes()
    # add the new section if it doesn't exist
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, 'host', options['host'])
    config.set(section, 'user', options['user'])
    config.set(section, 'geometry', options['geometry'])
    config.set(section, 'program', options['program'])
    config.set(section, 'homeshare', options['homeshare'])
    config.set(section, 'grabkeyboard', options['grabkeyboard'])
    config.set(section, 'fullscreen', options['fullscreen'])
    write_config()


def delete_config(section):
    config.remove_section(section)
    write_config()


# Set options based on config file
def read_config(section):
    if os.path.exists(configfile):
        options['host'] = config.get(section, 'host')
        options['user'] = config.get(section, 'user')
        options['geometry'] = config.get(section, 'geometry')
        options['program'] = config.get(section, 'program')
        options['homeshare'] = config.get(section, 'homeshare')
        options['grabkeyboard'] = config.get(section, 'grabkeyboard')
        options['fullscreen'] = config.get(section, 'fullscreen')


# Make a list of all profiles in config file.  Sort the order alphabetically,
# except 'defaults' always comes first
def list_profiles():
    profiles_list = sorted(config.sections())
    defaults_index = profiles_list.index('defaults')
    profiles_list.insert(0, profiles_list.pop(defaults_index))
    return profiles_list


# Run the selected RDP client - currently rdesktop or xfreerdp
def run_program(window):
    client_opts = {
        'rdesktop': {
            'stdopts': ['rdesktop', '-ken-us', '-a16'],
            'host': '',
            'user': '-u',
            'geometry': '-g',
            'homeshare': '-rdisk:home=' + os.environ['HOME'],
            'grabkeyboard': '-K',
            'fullscreen': '-f'
        },
        'xfreerdp': {
            'stdopts': ['xfreerdp', '/cert-ignore', '-sec-nla', '+clipboard'],
            'host': '/v:',
            'user': '/u:',
            'geometry': '/size:',
            'homeshare': '+home-drive',
            'grabkeyboard': '-grab-keyboard',
            'fullscreen': '/f'
        }
    }

    # This makes the next bit a little cleaner name-wise
    client = options['program']
    # List of commandline paramenters for our RDP client
    params = []
    # Add standard options to the parameter list
    for x in client_opts[client]['stdopts']:
        params.append(x)
    # Throw an error if the required host field is empty
    if not options['host']:
        window.on_warn(None, 'No Host', 'No Host or IP Address Given')
        return
    # Add specified options to the parameter list
    if options['user'] != '':
        params.append(client_opts[client]['user']
                      + '%s' % string.strip(options['user']))
    if options['geometry'] != '':
        if options['geometry'].find('%') == -1:
            params.append(client_opts[client]['geometry']
                          + '%s' % string.strip(options['geometry']))
        else:
            params.append(client_opts[client]['geometry']
                          + window.geo_percent(options['geometry']))
    if options['fullscreen'] == 'true':
        params.append(client_opts[client]['fullscreen'])
    if options['grabkeyboard'] == 'false':
        params.append(client_opts[client]['grabkeyboard'])
    if options['homeshare'] == 'true':
        params.append(client_opts[client]['homeshare'])
    params.append(client_opts[client]['host']
                  + '%s' % string.strip(options['host']))
    # Print the command line that we constructed to the terminal
    print 'Command to execute: \n' + ' '.join(str(param) for param in params)
    # Make it go!
    p = subprocess.Popen(params, stderr=subprocess.PIPE)
    # Wait for DNS resolution or connection failures
    time.sleep(1)
    # If RDP client died, display stderr via popup
    if p.poll() is not None:
        window.on_warn(None, 'Connection Error', '%s: \n' % client +
                       p.communicate()[1])


# GUI stuff
class MainWindow(Gtk.Window):
    def __init__(self):
        # Window properties
        Gtk.Window.__init__(self, title="Rocket Depot", resizable=0)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(8)
        self.set_wmclass('rocket-depot', 'rocket-depot')

        # Menu bar
        action_group = Gtk.ActionGroup("Menu")
        self.add_file_menu_actions(action_group)
        self.add_help_menu_actions(action_group)
        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)
        menubar = uimanager.get_widget("/MenuBar")

        # Grid for widgets in main window
        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        self.add(grid)

        # Labels for text entry fields and comboboxes
        profileslabel = Gtk.Label("Profile")
        hostlabel = Gtk.Label("Host")
        userlabel = Gtk.Label("Username")
        geometrylabel = Gtk.Label("Geometry")
        programlabel = Gtk.Label("RDP Client")

        # Adding our list of profiles to the combobox.
        self.profiles_combo = Gtk.ComboBoxText.new_with_entry()
        self.populate_profiles_combobox()
        self.profiles_combo.connect("changed", self.on_profiles_combo_changed)

        # Text entry fields
        self.hostentry = Gtk.Entry()
        self.hostentry.connect("activate", self.enter_connect, self.hostentry)
        self.userentry = Gtk.Entry()
        self.userentry.connect("activate", self.enter_connect, self.userentry)
        self.geometryentry = Gtk.Entry()
        self.geometryentry.connect("activate",
                                   self.enter_connect, self.geometryentry)

        # Combobox for program selection
        program_store = Gtk.ListStore(str)
        self.programs = {'rdesktop': 1, 'xfreerdp': 0}

        # Adding our list of programs to the combobox.  We add these boolean
        # values since the widget needs a boolean to define which selection is
        # active
        for key in self.programs:
            program_store.append([key])
        self.program_combo = Gtk.ComboBox.new_with_model(program_store)
        self.program_combo.connect("changed", self.on_program_combo_changed)
        self.program_renderer_text = Gtk.CellRendererText()
        self.program_combo.pack_start(self.program_renderer_text, True)
        self.program_combo.add_attribute(self.program_renderer_text, "text", 0)

        # Checkbox for sharing our home directory
        self.homedirbutton = Gtk.CheckButton("Share Home Dir")
        self.homedirbutton.connect("toggled", self.on_button_toggled,
                                   "homeshare")

        # Checkbox for grabbing the keyboard
        self.grabkeyboardbutton = Gtk.CheckButton("Grab Keyboard")
        self.grabkeyboardbutton.connect("toggled", self.on_button_toggled,
                                        "grabkeyboard")

        # Checkbox for fullscreen view
        self.fullscreenbutton = Gtk.CheckButton("Fullscreen")
        self.fullscreenbutton.connect("toggled", self.on_button_toggled,
                                      "fullscreen")

        # Quit button
        quitbutton = Gtk.Button(label="Quit")
        quitbutton.connect("clicked", self.quit)

        # Connect button
        connectbutton = Gtk.Button(label="Connect")
        connectbutton.connect("clicked", self.enter_connect)

        # Grid to which we attach all of our widgets
        grid.attach(menubar, 0, 0, 12, 4)
        grid.attach(profileslabel, 0, 4, 4, 4)
        grid.attach(hostlabel, 0, 8, 4, 4)
        grid.attach(userlabel, 0, 12, 4, 4)
        grid.attach(geometrylabel, 0, 16, 4, 4)
        grid.attach(programlabel, 0, 20, 4, 4)
        grid.attach_next_to(self.profiles_combo, profileslabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.hostentry, hostlabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.userentry, userlabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.geometryentry, geometrylabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.program_combo, programlabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach(self.homedirbutton, 0, 24, 4, 4)
        grid.attach_next_to(self.grabkeyboardbutton, self.homedirbutton,
                            Gtk.PositionType.RIGHT, 4, 4)
        grid.attach_next_to(self.fullscreenbutton, self.grabkeyboardbutton,
                            Gtk.PositionType.RIGHT, 4, 4)
        grid.attach(quitbutton, 0, 28, 4, 4)
        grid.attach_next_to(connectbutton, quitbutton,
                            Gtk.PositionType.RIGHT, 8, 4)

        # Define initial profile data
        self.load_settings()
        self.profilename = 'defaults'
        # Set up Unity quicklist
        if unity is True:
            self.create_unity_quicklist()

    def geo_percent(self, geometry):
        cleangeo = int(re.sub('[^0-9]', '', geometry))
        # Get the screen from the GtkWindow
        screen = self.get_screen()
        # Using the screen of the Window, the monitor it's on can be identified
        monitor = screen.get_monitor_at_window(screen.get_active_window())
        # Then get the geometry of that monitor
        mongeometry = screen.get_monitor_geometry(monitor)
        cleangeo /= 100.
        width = int(round(cleangeo * mongeometry.width))
        height = int(round(cleangeo * mongeometry.height))
        return "%sx%s" % (width, height)

    def populate_profiles_combobox(self):
        self.profiles_combo.get_model().clear()
        for profile in list_profiles():
            if profile != 'defaults':
                self.profiles_combo.append_text(profile)

    def populate_unity_quicklist(self):
        for profile in list_profiles():
            self.update_unity_quicklist(profile)

    def create_unity_quicklist(self):
        self.um_launcher_entry = \
                                 Unity.LauncherEntry.get_for_desktop_id(
                                 "rocket-depot.desktop")
        self.quicklist = Dbusmenu.Menuitem.new()
        self.populate_unity_quicklist()
        self.um_launcher_entry.set_property("quicklist", self.quicklist)

    def update_unity_quicklist(self, profile):
        if profile != 'defaults':
            profile_menu_item = Dbusmenu.Menuitem.new()
            profile_menu_item.property_set(Dbusmenu.MENUITEM_PROP_LABEL,
                                           profile)
            profile_menu_item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE,
                                                True)
            profile_menu_item.connect("item-activated", self.on_unity_clicked,
                                      profile)
            self.quicklist.child_append(profile_menu_item)

    def clean_unity_quicklist(self):
        for x in self.quicklist.get_children():
            self.quicklist.child_delete(x)
        self.populate_unity_quicklist()

    # Triggered when the connect button is clicked
    def on_unity_clicked(self, widget, entry, profile):
        read_config(profile)
        run_program(self)

    def enter_connect(self, *args):
        self.grab_textboxes()
        run_program(self)

    # Triggered when the combobox is clicked
    def on_profiles_combo_changed(self, combo):
        text = combo.get_active_text()
        for profile in list_profiles():
            if text == profile:
                read_config(text)
                self.load_settings()
        self.profilename = text

    # Triggered when the combobox is clicked
    def on_program_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            program = model[tree_iter][0]
        options['program'] = program

    # Triggered when the checkboxes are toggled
    def on_button_toggled(self, button, name):
        if button.get_active():
            state = 'true'
            options[name] = state
        else:
            state = 'false'
            options[name] = state

    # Triggered when the file menu is used
    def add_file_menu_actions(self, action_group):
        action_filemenu = Gtk.Action("FileMenu", "File", None, None)
        action_group.add_action(action_filemenu)
        # Why do the functions here execute on startup if we add parameters?
        action_group.add_actions([("SaveCurrentConfig", None,
                                   "Save Current Profile", None, None,
                                   self.save_current_config)])
        action_group.add_actions([("SaveCurrentConfigAsDefault", None,
                                   "Save Current Profile as Default", None,
                                   None, self.save_current_config_as_default)])
        action_group.add_actions([("DeleteCurrentConfig", None,
                                   "Delete Current Profile", None, None,
                                   self.delete_current_config)])
        action_filequit = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.quit)
        action_group.add_action(action_filequit)

    # Triggered when the help menu is used
    def add_help_menu_actions(self, action_group):
        action_group.add_actions([
            ("Help", None, "Help"),
            ("About", None, "About", None, None,
             self.on_menu_help),
        ])

    # Needed for the menu bar, I think
    def create_ui_manager(self):
        uimanager = Gtk.UIManager()
        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)
        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    # When the save config button is clicked on the menu bar
    def save_current_config(self, widget):
        if self.profilename == '' or self.profilename == 'defaults':
            self.on_warn(None, 'No Profile Name',
                         'Please name your profile before saving.')
        else:
            save_config(self.profilename, self)
            self.populate_profiles_combobox()
            if unity is True:
                self.update_unity_quicklist(self.profilename)

    # When the delete config button is clicked on the menu bar
    def delete_current_config(self, widget):
        if self.profilename == '' or self.profilename == 'defaults':
            self.on_warn(None, 'Select a Profile',
                         'Please select a profile to delete.')
        else:
            delete_config(self.profilename)
            read_config('defaults')
            self.load_settings()
            self.profiles_combo.set_active(-1)
            self.profiles_combo.prepend_text('')
            self.profiles_combo.set_active(0)
            active = self.profiles_combo.get_active()
            self.profiles_combo.remove(active)
            self.populate_profiles_combobox()
            if unity is True:
                self.clean_unity_quicklist()

    # When the save config button is clicked on the menu bar
    def save_current_config_as_default(self, widget):
        save_config('defaults', self)

    # When the quit button is clicked on the menu bar
    def quit(self, widget):
        Gtk.main_quit()

    # When the help button is clicked on the menu bar
    def on_menu_help(self, widget):
        self.on_about(widget)

    # Grab all textbox input
    def grab_textboxes(self):
        options['host'] = self.hostentry.get_text()
        options['user'] = self.userentry.get_text()
        options['geometry'] = self.geometryentry.get_text()

    # Generic warning dialog
    def on_warn(self, widget, title, message):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
                                   Gtk.ButtonsType.OK, title,
                                   title='Rocket Depot')
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    # About dialog
    def on_about(self, widget):
        about = Gtk.AboutDialog()
        about.set_program_name("Rocket Depot")
        about.set_version("0.0")
        about.set_comments("rdesktop/xfreerdp Frontend")
        about.set_website("https://github.com/robled/rocket-depot")
        about.run()
        about.destroy()

    # Load all settings
    def load_settings(self):
        self.hostentry.set_text(options['host'])
        self.userentry.set_text(options['user'])
        self.geometryentry.set_text(options['geometry'])
        self.program_combo.set_active(self.programs[options['program']])
        if options['homeshare'] == 'true':
            self.homedirbutton.set_active(True)
        else:
            self.homedirbutton.set_active(False)
        if options['grabkeyboard'] == 'true':
            self.grabkeyboardbutton.set_active(True)
        else:
            self.grabkeyboardbutton.set_active(False)
        if options['fullscreen'] == 'true':
            self.fullscreenbutton.set_active(True)
        else:
            self.fullscreenbutton.set_active(False)


def _main():
    read_config('defaults')
    save_config('defaults')
    # Make the GUI!
    window = MainWindow()
    window.connect("delete-event", Gtk.main_quit)
    window.show_all()
    # Set focus to the host entry box on startup
    window.hostentry.grab_focus()
    Gtk.main()


if __name__ == '__main__':
    _main()
