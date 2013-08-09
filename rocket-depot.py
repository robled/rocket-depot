#!/usr/bin/env python

# Originally written by Cory Wright
# http://projects.standblue.net/software/#rdesktop-open

import os
import string
import ConfigParser
from gi.repository import Gtk, Gdk, GObject
from gi.repository.GdkPixbuf import Pixbuf

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
      <menuitem action='FileQuit' />
    </menu>
    <menu action='OptionMenu'>
      <menuitem action='PrintDebug' />
    </menu>
    <menu action='Help'>
      <menuitem action='About'/>
    </menu>
  </menubar>
</ui>
"""

OPTIONS_TEMPLATE = '''Currently selected options:
host = %(host)s
user = %(user)s
geometry = %(geometry)s
program = %(program)s
homeshare = %(homeshare)s
grabkeyboard = %(grabkeyboard)s
fullscreen = %(fullscreen)s
'''


# Write the config file
def save_config(section, configfile, window=None):
    # Add options specified in the GUI if it's available.
    # GUI is not available when we are running for the first time and are
    # creating the initial config file.
    config = read_config(section, configfile)

    if window:
        options['host'] = string.strip(window.hostentry.get_text())
        options['user'] = string.strip(window.userentry.get_text())
        options['geometry'] = string.strip(window.geometryentry.get_text())

    # add the 'defaults' section if it doesn't exist
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, 'host', options['host'])
    config.set(section, 'user', options['user'])
    config.set(section, 'geometry', options['geometry'])
    config.set(section, 'program', options['program'])
    config.set(section, 'homeshare', options['homeshare'])
    config.set(section, 'grabkeyboard', options['grabkeyboard'])
    config.set(section, 'fullscreen', options['fullscreen'])

    # Writing our configuration file
    with open(configfile, 'wb') as f:
        config.write(f)


# Set options based on config file
def read_config(section, configfile):
    # Create the config file if it doesn't exist, otherwise read the existing
    # file

    config = ConfigParser.RawConfigParser()
    config.read(configfile)

    if os.path.exists(configfile):
        options['host'] = config.get(section, 'host')
        options['user'] = config.get(section, 'user')
        options['geometry'] = config.get(section, 'geometry')
        options['program'] = config.get(section, 'program')
        if config.getboolean(section, 'homeshare'):
            options['homeshare'] = config.get(section, 'homeshare')
        if config.getboolean(section, 'grabkeyboard'):
            options['grabkeyboard'] = config.get(section, 'grabkeyboard')
        if config.getboolean(section, 'fullscreen'):
            options['fullscreen'] = config.get(section, 'fullscreen')

    return config


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

    client = options['program']

    # List of commandline paramenters for our RDP client
    params = []

    # Add standard options to the parameter list
    for x in client_opts[client]['stdopts']:
        params.append(x)

    # Throw an error if the required host field is empty
    if not options['host']:
        window.on_warn('null', 'No Host', 'No Host or IP Address Given')
        return

    # Add specified options to the parameter list
    if options['user'] != '':
        params.append(client_opts[client]['user']
                      + '%s' % string.strip(options['user']))
    if options['geometry'] != '':
        params.append(client_opts[client]['geometry']
                      + '%s' % string.strip(options['geometry']))
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
    os.spawnvp(os.P_NOWAIT, params[0], params)
    return


# Print the list of options currently selected for debugging
def print_options():
    print OPTIONS_TEMPLATE % options


# GUI stuff
class MainWindow(Gtk.Window):
    def __init__(self, configfile):
        self.configfile = configfile

        # Window properties
        Gtk.Window.__init__(self, title="rocket-depot", resizable=0)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(8)
        progicon = Gtk.IconTheme.get_default().load_icon('gnome-fs-web', 64, 0)
        self.set_icon(progicon)
        self.set_wmclass('rocket-depot', 'rocket-depot')

        # Menu bar
        action_group = Gtk.ActionGroup("Menu")
        self.add_file_menu_actions(action_group)
        self.add_options_menu_actions(action_group)
        self.add_help_menu_actions(action_group)
        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)
        menubar = uimanager.get_widget("/MenuBar")

        # Grid for widgets in main window
        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        self.add(grid)

        # Labels for text entry fields and comboboxes
        hostlabel = Gtk.Label("Host")
        userlabel = Gtk.Label("Username")
        geometrylabel = Gtk.Label("Geometry")
        programlabel = Gtk.Label("Program")

        # Text entry fields
        self.hostentry = Gtk.Entry()
        self.hostentry.set_text(options['host'])
        self.hostentry.connect("activate", self.enter_callback, self.hostentry)
        self.userentry = Gtk.Entry()
        self.userentry.set_text(options['user'])
        self.userentry.connect("activate", self.enter_callback, self.userentry)
        self.geometryentry = Gtk.Entry()
        self.geometryentry.set_text(options['geometry'])
        self.geometryentry.connect("activate",
                                   self.enter_callback, self.geometryentry)

        # Combobox for program selection
        program_store = Gtk.ListStore(str)
        programs = {'rdesktop': 1, 'xfreerdp': 0}

        # Adding our list of programs to the combobox.  We add these boolean
        # values since the widget needs a boolean to define which selection is
        # active
        for key in programs:
            program_store.append([key])
        program_combo = Gtk.ComboBox.new_with_model(program_store)
        program_combo.connect("changed", self.on_program_combo_changed)
        renderer_text = Gtk.CellRendererText()
        program_combo.pack_start(renderer_text, True)
        program_combo.add_attribute(renderer_text, "text", 0)
        program_combo.set_active(programs[options['program']])

        # Checkboxes for our toggle options
        # Checkbox for sharing our home directory
        homedirbutton = Gtk.CheckButton("Share Home Dir")
        homedirbutton.connect("toggled", self.on_button_toggled, "homeshare")
        if options['homeshare'] == 'true':
            homedirbutton.set_active(True)

        # Checkbox for grabbing the keyboard
        grabkeyboardbutton = Gtk.CheckButton("Grab Keyboard")
        grabkeyboardbutton.connect("toggled", self.on_button_toggled,
                                   "grabkeyboard")
        if options['grabkeyboard'] == 'true':
            grabkeyboardbutton.set_active(True)

        # Checkbox for fullscreen view
        fullscreenbutton = Gtk.CheckButton("Fullscreen")
        fullscreenbutton.connect("toggled", self.on_button_toggled,
                                 "fullscreen")
        if options['fullscreen'] == 'true':
            fullscreenbutton.set_active(True)

        # Quit button
        quitbutton = Gtk.Button(label="Quit")
        quitbutton.connect("clicked", self.on_menu_file_quit)

        # Connect button
        connectbutton = Gtk.Button(label="Connect")
        connectbutton.connect("clicked", self.on_connectbutton_clicked)

        # Grid to which we attach all of our widgets
        grid.attach(menubar, 0, 0, 12, 4)
        grid.attach(hostlabel, 0, 4, 4, 4)
        grid.attach(userlabel, 0, 8, 4, 4)
        grid.attach(geometrylabel, 0, 16, 4, 4)
        grid.attach(programlabel, 0, 20, 4, 4)
        grid.attach_next_to(self.hostentry, hostlabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.userentry, userlabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.geometryentry, geometrylabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(program_combo, programlabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach(homedirbutton, 0, 24, 4, 4)
        grid.attach_next_to(grabkeyboardbutton, homedirbutton,
                            Gtk.PositionType.RIGHT, 4, 4)
        grid.attach_next_to(fullscreenbutton, grabkeyboardbutton,
                            Gtk.PositionType.RIGHT, 4, 4)
        grid.attach(quitbutton, 0, 28, 4, 4)
        grid.attach_next_to(connectbutton, quitbutton,
                            Gtk.PositionType.RIGHT, 8, 4)

    # Triggered when the enter key is pressed on any text entry box
    def enter_callback(self, widget, entry):
        self.execute()

    # Triggered when the connect button is clicked
    def on_connectbutton_clicked(self, widget):
        self.execute()

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
        action_group.add_actions([("SaveCurrentConfig", None,
                                   "Save Current Configuration", None, None,
                                   self.on_menu_file_save_config)])
        action_filequit = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.on_menu_file_quit)
        action_group.add_action(action_filequit)

    # Triggered when the options menu is used
    def add_options_menu_actions(self, action_group):
        action_group.add_actions([
            ("OptionMenu", None, "Options"),
            ("PrintDebug", None, "Print Debugging to Terminal", None, None,
             self.on_menu_debug),
        ])

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
    def on_menu_file_save_config(self, widget):
        save_config('defaults', self.configfile, self)

    # When the quit button is clicked on the menu bar
    def on_menu_file_quit(self, widget):
        Gtk.main_quit()

    # When the help button is clicked on the menu bar
    def on_menu_help(self, widget):
        self.on_about(widget)

    # When the debug button is clicked on the menu bar
    def on_menu_debug(self, widget):
        options['host'] = self.hostentry.get_text()
        options['user'] = self.userentry.get_text()
        options['geometry'] = self.geometryentry.get_text()
        print_options()

    # Run our command line RDP client
    def execute(self):
        options['host'] = self.hostentry.get_text()
        options['user'] = self.userentry.get_text()
        options['geometry'] = self.geometryentry.get_text()
        run_program(self)

    # Generic info dialog
    def on_info(self, widget):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK,
                                   "This is an INFO MessageDialog",
                                   title='rocket-depot')
        dialog.format_secondary_text(
            "And this is the secondary text that explains things.")
        dialog.run()
        dialog.destroy()

    # Generic warning dialog
    def on_warn(self, widget, title, message):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
                                   Gtk.ButtonsType.OK, title,
                                   title='rocket-depot')
        dialog.format_secondary_text(message)
        response = dialog.run()
        dialog.destroy()

    # About dialog
    def on_about(self, widget):
        about = Gtk.AboutDialog()
        about.set_program_name("rocket-depot")
        about.set_version("0.0")
        about.set_comments("rdesktop/xfreerdp Frontend")
        about.set_website("https://github.com/robled/rocket-depot")
        about.run()
        about.destroy()


def _main():
    # Path to config file
    configfile = '%s/.rocket-depot' % os.environ['HOME']
    read_config('defaults', configfile)

    # Make the GUI!
    window = MainWindow(configfile)
    window.connect("delete-event", Gtk.main_quit)
    window.show_all()
    Gtk.main()
    save_config('defaults', configfile)

if __name__ == '__main__':
    _main()
