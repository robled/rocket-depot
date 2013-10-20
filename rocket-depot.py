#!/usr/bin/env python

import os
import re
import shlex
import subprocess
import threading
import time
import ConfigParser
from gi.repository import Gtk, GObject

# Begin thread stuff early
GObject.threads_init()

# Enable special features if we're running Ubuntu Unity
de = os.environ.get('DESKTOP_SESSION')
if de == 'ubuntu' or de == 'ubuntu-2d':
    from gi.repository import Unity, Dbusmenu
    unity = True
else:
    unity = False

# Local user homedir
homedir = os.environ['HOME']


# Create config dir
def create_config_dir():
    configdir = '%s/.config/rocket-depot' % homedir
    if not os.path.exists(configdir):
        try:
            os.mkdir(configdir, 0700)
        except OSError:
            print 'Error:  Unable to create config directory.'

# Our config dotfile
configfile = '%s/.config/rocket-depot/config.ini' % homedir
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


# Open the config file for writing
def write_config():
    with open(configfile, 'wb') as f:
        config.write(f)


# Save options to the config file
def save_config(section, window=None):
    # if the UI is running, let's see what's in the textboxes
    if window:
        window.grab_textboxes()
    # add the new section if it doesn't exist
    if not config.has_section(section):
        config.add_section(section)
    # Set all selected options
    config.set(section, 'host', options['host'])
    config.set(section, 'user', options['user'])
    config.set(section, 'geometry', options['geometry'])
    config.set(section, 'program', options['program'])
    config.set(section, 'homeshare', options['homeshare'])
    config.set(section, 'grabkeyboard', options['grabkeyboard'])
    config.set(section, 'fullscreen', options['fullscreen'])
    write_config()


# Delete a section from the config file
def delete_config(section):
    config.remove_section(section)
    write_config()


# Set options based on section in config file
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
# except special 'defaults' profile always comes first
def list_profiles():
    profiles_list = sorted(config.sections())
    defaults_index = profiles_list.index('defaults')
    profiles_list.insert(0, profiles_list.pop(defaults_index))
    return profiles_list


# Run the selected RDP client - currently rdesktop or xfreerdp
def run_program(window):
    # CLI parameters for each RDP client we support.  stdopts are always used.
    client_opts = {
        'rdesktop': {
            'stdopts': ['rdesktop', '-ken-us', '-a16'],
            'host': '',
            'user': '-u',
            'geometry': '-g',
            'homeshare': '-rdisk:home=' + homedir,
            'grabkeyboard': '-K',
            'fullscreen': '-f'
        },
        'xfreerdp': {
            'stdopts': ['xfreerdp', '--no-nla', '--plugin', 'cliprdr'],
            'host': '',
            'user': '-u',
            'geometry': '-g',
            'homeshare': '--plugin rdpdr --data disk:home:' + homedir + ' --',
            'grabkeyboard': '-K',
            'fullscreen': '-f'
        }
    }

    # This makes the next bit a little cleaner name-wise
    global client
    client = options['program']
    # List of commandline paramenters for our RDP client
    params = []
    # Add standard options to the parameter list
    for x in client_opts[client]['stdopts']:
        params.append(x)
    # Add specified options to the parameter list
    if options['user'] != '':
        params.append(client_opts[client]['user'])
        # We put quotes around the username so that the domain\username format
        # doesn't get escaped
        params.append("'%s'" % str.strip(options['user']))
    # Detect percent symbol in geometry field.  If it exists we do math to
    # use the correct resolution for the active monitor.  Otherwise we submit
    # a given resolution such as 1024x768 to the list of parameters.
    if options['geometry'] != '':
        if options['geometry'].find('%') == -1:
            params.append(client_opts[client]['geometry'])
            params.append('%s' % str.strip(options['geometry']))
        else:
            params.append(client_opts[client]['geometry'])
            params.append(window.geo_percent(options['geometry']))
    if options['fullscreen'] == 'true':
        params.append(client_opts[client]['fullscreen'])
    if options['grabkeyboard'] == 'false':
        params.append(client_opts[client]['grabkeyboard'])
    if options['homeshare'] == 'true':
        params.append(client_opts[client]['homeshare'])
    # Hostname goes last in the list of parameters
    params.append(client_opts[client]['host']
                  + '%s' % str.strip(options['host']))
    # Clean up params list to make it shell compliant
    cmdline = shlex.split(' '.join(params))
    # Print the command line that we constructed to the terminal
    print 'Command to execute: \n' + ' '.join(str(x) for x in cmdline)
    return cmdline


class WorkerThread(threading.Thread):
    def __init__(self, callback, cmdline):
        threading.Thread.__init__(self)
        self.callback = callback
        self.cmdline = cmdline

    def run(self):
        global p
        p = subprocess.Popen(self.cmdline, stderr=subprocess.PIPE)
        time.sleep(2)
        GObject.idle_add(self.callback)


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

        # Profiles combobox
        self.profiles_combo = Gtk.ComboBoxText.new_with_entry()
        self.profiles_combo.set_tooltip_text('List of saved connection '
                                             'profiles')
        self.populate_profiles_combobox()
        self.profiles_combo.connect("changed", self.on_profiles_combo_changed)
        # If an existing profile name has been typed into the profiles
        # combobox, allow the 'enter' key to launch the RDP client
        profiles_combo_entry = self.profiles_combo.get_children()[0]
        profiles_combo_entry.connect("activate", self.enter_connect,
                                     profiles_combo_entry)

        # Text entry fields
        self.hostentry = Gtk.Entry()
        self.hostentry.set_tooltip_text('Hostname or IP address of RDP server')
        self.hostentry.connect("activate", self.enter_connect, self.hostentry)
        self.userentry = Gtk.Entry()
        self.userentry.set_tooltip_text('''RDP username.
Domain credentials may be entered in domain\username format:
e.g. "example.com\myusername"''')
        self.userentry.connect("activate", self.enter_connect, self.userentry)
        self.geometryentry = Gtk.Entry()
        self.geometryentry.set_tooltip_text('''Resolution of RDP window.
Can be set to a specific resolution or a percentage:
e.g. "1024x768" or "80%"''')
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
        self.program_combo.set_tooltip_text('List of supported RDP clients')
        self.program_combo.connect("changed", self.on_program_combo_changed)
        self.program_renderer_text = Gtk.CellRendererText()
        self.program_combo.pack_start(self.program_renderer_text, True)
        self.program_combo.add_attribute(self.program_renderer_text, "text", 0)

        # Checkbox for sharing our home directory
        self.homedirbutton = Gtk.CheckButton("Share Home Dir")
        self.homedirbutton.set_tooltip_text('Share local home directory with '
                                            'RDP server')
        self.homedirbutton.connect("toggled", self.on_button_toggled,
                                   "homeshare")

        # Checkbox for grabbing the keyboard
        self.grabkeyboardbutton = Gtk.CheckButton("Grab Keyboard")
        self.grabkeyboardbutton.set_tooltip_text('Send all keyboard inputs to '
                                                 'RDP server')
        self.grabkeyboardbutton.connect("toggled", self.on_button_toggled,
                                        "grabkeyboard")

        # Checkbox for fullscreen view
        self.fullscreenbutton = Gtk.CheckButton("Fullscreen")
        self.fullscreenbutton.set_tooltip_text('Run RDP client in fullscreen '
                                               'mode')
        self.fullscreenbutton.connect("toggled", self.on_button_toggled,
                                      "fullscreen")

        # Quit button
        quitbutton = Gtk.Button(label="Quit")
        quitbutton.connect("clicked", self.quit)

        # Connect button
        self.connectbutton = Gtk.Button(label="Connect")
        self.connectbutton.connect("clicked", self.enter_connect)

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
        grid.attach_next_to(self.connectbutton, quitbutton,
                            Gtk.PositionType.RIGHT, 8, 4)

        # Load the default profile on startup
        self.load_settings()
        self.profilename = 'defaults'
        # Set up Unity quicklist if we can support that
        if unity is True:
            self.create_unity_quicklist()

    # If a geometry percentage is given, let's figure out the actual resolution
    def geo_percent(self, geometry):
        # Remove the percent symbol from our value
        cleangeo = int(re.sub('[^0-9]', '', geometry))
        # Get the screen from the GtkWindow
        screen = self.get_screen()
        # Using the screen of the Window, the monitor it's on can be identified
        monitor = screen.get_monitor_at_window(screen.get_active_window())
        # Then get the geometry of that monitor
        mongeometry = screen.get_monitor_geometry(monitor)
        # Move our geometry percent decimal place two to the left so that we
        # can multiply
        cleangeo /= 100.
        # Multiply current width and height to find requested width and height
        width = int(round(cleangeo * mongeometry.width))
        height = int(round(cleangeo * mongeometry.height))
        return "%sx%s" % (width, height)

    # Each section in the config file gets an entry in the profiles combobox
    def populate_profiles_combobox(self):
        self.profiles_combo.get_model().clear()
        for profile in list_profiles():
            if profile != 'defaults':
                self.profiles_combo.append_text(profile)

    # Each section in the config file gets an entry in the Unity quicklist
    def populate_unity_quicklist(self):
        for profile in list_profiles():
            self.update_unity_quicklist(profile)

    # Create the Unity quicklist and populate it with our profiles
    def create_unity_quicklist(self):
        entry = Unity.LauncherEntry.get_for_desktop_id("rocket-depot.desktop")
        self.quicklist = Dbusmenu.Menuitem.new()
        self.populate_unity_quicklist()
        entry.set_property("quicklist", self.quicklist)

    # Append a new profile to the Unity quicklist
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

    # If we delete a profile we must delete all Unity quicklist entries and
    # rebuild the quicklist
    def clean_unity_quicklist(self):
        for x in self.quicklist.get_children():
            self.quicklist.child_delete(x)
        self.populate_unity_quicklist()

    def start_thread(self):
        # Throw an error if the required host field is empty
        if not options['host']:
            self.on_warn(None, 'No Host', 'No Host or IP Address Given')
        else:
            self.connectbutton.set_sensitive(False)
            cmdline = run_program(self)
            thread = WorkerThread(self.work_finished_cb, cmdline)
            thread.start()

    # Triggered when a profile is selected via the Unity quicklist
    def on_unity_clicked(self, widget, entry, profile):
        read_config(profile)
        self.start_thread()

    # Trigged when we press 'Enter' or the 'Connect' button
    def enter_connect(self, *args):
        self.grab_textboxes()
        self.start_thread()

    def work_finished_cb(self):
        #self.spinner.stop()
        if p.poll() is not None:
            self.on_warn(None, 'Connection Error', '%s: \n' % client +
                           p.communicate()[1])
        self.connectbutton.set_sensitive(True)

    # Triggered when the combobox is clicked.  We load the selected profile
    # from the config file.
    def on_profiles_combo_changed(self, combo):
        text = combo.get_active_text()
        for profile in list_profiles():
            if text == profile:
                read_config(text)
                self.load_settings()
        self.profilename = text

    # Triggered when the combobox is clicked.  We set the selected RDP client.
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

    # Needed for the menu bar
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
                self.clean_unity_quicklist()

    # When the delete config button is clicked on the menu bar
    def delete_current_config(self, widget):
        if self.profilename == '' or self.profilename == 'defaults':
            self.on_warn(None, 'Select a Profile',
                         'Please select a profile to delete.')
        else:
            delete_config(self.profilename)
            # reload the default config
            read_config('defaults')
            self.load_settings()
            # Set profiles combobox to have no active item
            self.profiles_combo.set_active(-1)
            # Add a blank string to the head end of the combobox to 'clear' it
            self.profiles_combo.prepend_text('')
            # Set the blank string active to again, to 'clear' the combobox
            self.profiles_combo.set_active(0)
            # Now that we've 'cleared' the combobox text, let's delete the
            # blank entry and then repopulate the entire combobox
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
        about.set_version("0.12")
        about.set_copyright("2013 David Roble")
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
    # Read the default profile and then save it if it doesn't already exist
    create_config_dir()
    read_config('defaults')
    save_config('defaults')
    # Make the GUI!
    global window
    window = MainWindow()
    window.connect("delete-event", Gtk.main_quit)
    window.show_all()
    # Set focus to the host entry box on startup
    window.hostentry.grab_focus()
    Gtk.main()


if __name__ == '__main__':
    _main()
