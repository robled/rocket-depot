#!/usr/bin/env python

import os
import re
import shlex
import subprocess
import sys
import threading
import time
import webbrowser
import ConfigParser
from gi.repository import GLib, GdkPixbuf, Gtk
# Import special features if we're running Ubuntu Unity
if (os.environ.get('DESKTOP_SESSION') == 'ubuntu' or
        os.environ.get('DESKTOP_SESSION') == 'ubuntu-2d'):
    from gi.repository import Unity, Dbusmenu
    unity = True
else:
    unity = False


class RocketDepot:
    def __init__(self):
        self.debug = False
        self.debug_cmdline()
        # Default options.  Overridden by config file.
        self.options = {
            'host': '',
            # set the default RDP user to the local user by default
            'user': os.environ.get('USER', 'user'),
            'geometry': '1024x768',
            'program': 'xfreerdp',
            'homeshare': 'false',
            'grabkeyboard': 'false',
            'fullscreen': 'false',
            'clioptions': '',
            'terminal': 'false'
        }
        # Local user homedir and config file
        self.homedir = os.environ['HOME']
        self.create_config_dir()
        # Our config dotfile
        self.configfile = '%s/.config/rocket-depot/config.ini' % self.homedir
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.configfile)
        self.read_config('DEFAULT')
        self.save_config('DEFAULT')
        self.saved_hosts = self.list_saved_hosts()
        self.mw = MainWindow(self)

    def debug_cmdline(self):
        '''A simple graphical frontend for rdesktop and FreeRDP

Usage: rocket-depot [--debug]
'''
        try:
            arg = sys.argv[1]
            if arg == '--debug':
                self.debug = True
            else:
                print self.debug_cmdline.__doc__
                sys.exit(1)
        except IndexError:
            self.debug = False

    # Create config dir
    def create_config_dir(self):
        configdir = '%s/.config/rocket-depot' % self.homedir
        if not os.path.exists(configdir):
            try:
                os.mkdir(configdir, 0700)
            except OSError:
                if self.debug:
                    print 'Error:  Unable to create config directory.'

    # Open the config file for writing
    def write_config(self):
        with open(self.configfile, 'wb') as f:
            self.config.write(f)

    # Save options to the config file
    def save_config(self, host):
    # add the new section if it doesn't exist
        if (not self.config.has_section(host) and
                host != 'DEFAULT' and host != ''):
            self.config.add_section(host)
        # Set all selected options
        for opt in self.options:
            if opt != 'host':
                self.config.set(host, opt, self.options[opt])
        self.write_config()
        self.saved_hosts = self.list_saved_hosts()

    # Delete a section from the config file
    def delete_config(self, host):
        self.config.remove_section(host)
        self.write_config()
        self.saved_hosts = self.list_saved_hosts()

    # Set options based on section in config file
    def read_config(self, host):
        if os.path.exists(self.configfile):
            for opt in self.options:
                if not self.config.has_option(host, opt):
                    self.options[opt] = ''
                else:
                    self.options[opt] = self.config.get(host, opt)
            if host == 'DEFAULT':
                self.options['host'] = ''
            else:
                self.options['host'] = host

    # Make a list of all hosts in config file.  Sort the order
    # alphabetically, except special 'DEFAULT' host always comes first
    def list_saved_hosts(self):
        hosts = sorted(self.config.sections())
        return hosts

    # Check for given host in freerdp's known_hosts file before connecting
    def check_known_hosts(self, host):
        known_hosts = '%s/.config/freerdp/known_hosts' % self.homedir
        try:
            with open(known_hosts, 'r') as f:
                read_data = f.read()
            match = re.search(host, read_data)
            if match:
                return True
            else:
                return False
        except IOError:
            return False

    # Run the selected RDP client - currently rdesktop or xfreerdp
    def run_program(self):
        # CLI parameters for each RDP client we support.  stdopts are always
        # used.
        client_opts = {
            'rdesktop': {
                'stdopts': ['rdesktop', '-a16'],
                'host': '',
                'user': '-u',
                'geometry': '-g',
                'homeshare': '-rdisk:home=' + self.homedir,
                'grabkeyboard': '-K',
                'fullscreen': '-f'
            },
            'xfreerdp': {
                'stdopts': ['xfreerdp', '+clipboard'],
                'host': '/v:',
                'user': '/u:',
                'geometry': '/size:',
                'homeshare': '/drive:home,' + self.homedir,
                'grabkeyboard': '-grab-keyboard',
                'fullscreen': '/f'
            }
        }

        # This makes the next bit a little cleaner name-wise
        client = self.options['program']
        # List of commandline paramenters for our RDP client
        params = []
        # Add standard options to the parameter list
        for x in client_opts[client]['stdopts']:
            params.append(x)
        # Add specified options to the parameter list
        if self.options['user'] != '':
            # We put quotes around the username so that the domain\username
            # format doesn't get escaped
            slashuser = "'%s'" % str.strip(self.options['user'])
            params.append(client_opts[client]['user'] + slashuser)
        # Detect percent symbol in geometry field.  If it exists we do math to
        # use the correct resolution for the active monitor.  Otherwise we
        # submit a given resolution such as 1024x768 to the list of parameters.
        if self.options['geometry'] != '':
            geo = client_opts[client]['geometry']
            if self.options['geometry'].find('%') == -1:
                params.append(geo
                              + '%s' % str.strip(self.options['geometry']))
            else:
                params.append(geo
                              + self.mw.geo_percent(self.options['geometry']))
        if self.options['fullscreen'] == 'true':
            params.append(client_opts[client]['fullscreen'])
        if self.options['grabkeyboard'] == 'false':
            params.append(client_opts[client]['grabkeyboard'])
        if self.options['homeshare'] == 'true':
            params.append(client_opts[client]['homeshare'])
        if self.options['clioptions'] != '':
            params.append(self.options['clioptions'])
        # Hostname goes last in the list of parameters
        params.append(client_opts[client]['host']
                      + '%s' % str.strip(self.options['host']))
        # Clean up params list to make it shell compliant
        cmdline = shlex.split(' '.join(params))
        self.terminal_needed(self.options['host'], cmdline)
        return cmdline

    # Open a terminal when freerdp needs user input
    def terminal_needed(self, host, cmdline):
        terminal_args = ['xterm', '-hold', '-e']

        def prepend_terminal():
            if cmdline[0] != terminal_args[0]:
                for x in reversed(terminal_args):
                    cmdline.insert(0, x)
        if cmdline[0] == 'xfreerdp':
            if '-sec-nla' not in cmdline:
                prepend_terminal()
            if ('/cert-ignore' not in cmdline and
                    self.check_known_hosts(host) is False):
                prepend_terminal()
        if self.options['terminal'] == 'true':
            prepend_terminal()


# Thread for RDP client launch feedback in UI
class WorkerThread(threading.Thread):
    def __init__(self, callback, cmdline):
        threading.Thread.__init__(self)
        self.callback = callback
        self.cmdline = cmdline
        WorkerThread.error_text = ''
        WorkerThread.return_code = 0

    # Start the client and wait some seconds for errors
    def run(self):
        p = subprocess.Popen(self.cmdline, stderr=subprocess.PIPE)
        start_time = time.time()
        while p.poll() is None:
            time.sleep(1)
            if time.time() - start_time > 3:
                break
        if p.poll() is not None:
            WorkerThread.error_text += p.communicate()[1]
            WorkerThread.return_code += p.returncode
        GLib.idle_add(self.callback)


# GUI stuff
class MainWindow(Gtk.Window):
    def __init__(self, rd):
        # Window properties
        self.rd = rd
        Gtk.Window.__init__(self, title="Rocket Depot", resizable=0)
        self.set_border_width(0)
        self.set_wmclass('rocket-depot', 'rocket-depot')
        self.program_icon = GdkPixbuf.Pixbuf.new_from_file("/usr/share/icons/hicolor/scalable/apps/rocket-depot.svg")
        self.set_icon(self.program_icon)

        # Menu bar layout
        self.UI_INFO = """
        <ui>
          <menubar name='MenuBar'>
            <menu action='FileMenu'>
              <menuitem action='SaveCurrentConfig' />
              <menuitem action='SaveCurrentConfigAsDefault' />
              <menuitem action='DeleteCurrentConfig' />
              <menuitem action='FileQuit' />
            </menu>
            <menu action='Help'>
              <menuitem action='FreeRDPDocs'/>
              <menuitem action='rdesktopDocs'/>
              <menuitem action='About'/>
            </menu>
          </menubar>
        </ui>
        """

        # Menu bar
        action_group = Gtk.ActionGroup(name="Menu")
        self.add_file_menu_actions(action_group)
        self.add_help_menu_actions(action_group)
        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)
        self.menubar = uimanager.get_widget("/MenuBar")

        # Labels for text entry fields and comboboxes
        hostlabel = Gtk.Label(label="Host")
        userlabel = Gtk.Label(label="Username")
        geometrylabel = Gtk.Label(label="Geometry")
        clioptionslabel = Gtk.Label(label="CLI Options")
        programlabel = Gtk.Label(label="RDP Client")

        # Host combobox
        self.host_combo_store = Gtk.ListStore(str)
        self.populate_host_combobox()
        self.host_combo = Gtk.ComboBox.new_with_model_and_entry(self.host_combo_store)
        self.host_combo.connect("changed", self.on_host_combo_changed)
        self.host_combo.set_entry_text_column(0)
        self.host_combo.set_tooltip_text('Enter hostname/IP or list saved hosts')
        self.host_entry = self.host_combo.get_child()
        # Auto-complete
        completion = Gtk.EntryCompletion()
        completion.set_model(self.host_combo_store)
        self.host_entry.set_completion(completion)
        completion.set_text_column(0)
        #completion.connect('match-selected', self.match_cb)
        completion.set_inline_completion(True)
        #entry.connect('activate', self.activate_cb)
        # If an existing hostname has been typed into the host
        # combobox, allow the 'enter' key to launch the RDP client
        host_combo_entry = self.host_combo.get_children()[0]
        host_combo_entry.connect("activate", self.enter_connect,
                                 host_combo_entry)

        # Text entry fields
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
        self.clioptionsentry = Gtk.Entry()
        self.clioptionsentry.set_tooltip_text('''Extra CLI options''')
        self.clioptionsentry.connect("activate",
                                     self.enter_connect, self.clioptionsentry)

        # Radio button for program selection
        self.xfreerdpbutton = Gtk.RadioButton.new_with_label_from_widget(None, "FreeRDP")
        self.xfreerdpbutton.connect("toggled", self.on_radio_button_toggled,
                                    "xfreerdp")
        self.rdesktopbutton = Gtk.RadioButton.new_from_widget(self.xfreerdpbutton)
        self.rdesktopbutton.set_label("rdesktop")
        self.rdesktopbutton.connect("toggled", self.on_radio_button_toggled,
                                    "rdesktop")
        self.xfreerdpbutton.set_tooltip_text('Choose a supported RDP client')
        self.rdesktopbutton.set_tooltip_text('Choose a supported RDP client')

        # Checkbox for sharing our home directory
        self.homedirbutton = Gtk.CheckButton(label="Share Home Dir")
        self.homedirbutton.set_tooltip_text('Share local home directory with '
                                            'RDP server')
        self.homedirbutton.connect("toggled", self.on_button_toggled,
                                   "homeshare")

        # Checkbox for grabbing the keyboard
        self.grabkeyboardbutton = Gtk.CheckButton(label="Grab Keyboard")
        self.grabkeyboardbutton.set_tooltip_text('Send all keyboard inputs to '
                                                 'RDP server')
        self.grabkeyboardbutton.connect("toggled", self.on_button_toggled,
                                        "grabkeyboard")

        # Checkbox for fullscreen view
        self.fullscreenbutton = Gtk.CheckButton(label="Fullscreen")
        self.fullscreenbutton.set_tooltip_text('Run RDP client in fullscreen '
                                               'mode')
        self.fullscreenbutton.connect("toggled", self.on_button_toggled,
                                      "fullscreen")

        # Checkbox for terminal
        self.terminalbutton = Gtk.CheckButton(label="Terminal")
        self.terminalbutton.set_tooltip_text('''Run RDP client from terminal.
Useful for diagnosing connection problems''')
        self.terminalbutton.connect("toggled", self.on_button_toggled,
                                    "terminal")

        # Progress spinner
        self.spinner = Gtk.Spinner()

        # Connect button
        self.connectbutton = Gtk.Button(label="Connect")
        self.connectbutton.connect("clicked", self.enter_connect)

        # Status bar
        self.status_bar = Gtk.Statusbar()

        # Frame for box provides a border for the grid
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.set_border_width(4)

        # Grid for widgets in main window
        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        frame.add(grid)

        # Root box for widgets
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.pack_start(self.menubar, False, False, 0)
        self.add(box)
        box.pack_start(frame, False, False, 0)
        hseparator = Gtk.HSeparator()
        box.pack_start(hseparator, False, False, 0)
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        status_box.pack_start(self.status_bar, False, False, 0)
        status_box.pack_end(self.spinner, False, False, 10)
        box.pack_end(status_box, False, False, 0)

        # Grid to which we attach all of our widgets
        grid.attach(hostlabel, 0, 0, 4, 4)
        grid.attach(userlabel, 0, 4, 4, 4)
        grid.attach(geometrylabel, 0, 8, 4, 4)
        grid.attach(clioptionslabel, 0, 12, 4, 4)
        grid.attach(programlabel, 0, 16, 4, 4)
        grid.attach(self.homedirbutton, 0, 20, 4, 4)
        grid.attach(self.terminalbutton, 0, 24, 4, 4)
        grid.attach_next_to(self.host_combo, hostlabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.userentry, userlabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.geometryentry, geometrylabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.clioptionsentry, clioptionslabel,
                            Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.xfreerdpbutton, programlabel,
                            Gtk.PositionType.RIGHT, 4, 4)
        grid.attach_next_to(self.rdesktopbutton, self.xfreerdpbutton,
                            Gtk.PositionType.RIGHT, 4, 4)
        grid.attach_next_to(self.grabkeyboardbutton, self.homedirbutton,
                            Gtk.PositionType.RIGHT, 4, 4)
        grid.attach_next_to(self.fullscreenbutton, self.grabkeyboardbutton,
                            Gtk.PositionType.RIGHT, 4, 4)
        grid.attach_next_to(self.connectbutton, self.terminalbutton,
                            Gtk.PositionType.RIGHT, 8, 4)

        # Load the default host on startup
        self.rd.options['host'] = 'DEFAULT'
        self.load_settings()
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

    # Each section in the config file gets an entry in the host combobox
    def populate_host_combobox(self):
        self.host_combo_store.clear()
        for host in self.rd.saved_hosts:
            if host != 'DEFAULT':
                self.host_combo_store.append([host])

    # Each section in the config file gets an entry in the Unity quicklist
    def populate_unity_quicklist(self):
        for host in self.rd.saved_hosts:
            self.update_unity_quicklist(host)

    # Create the Unity quicklist and populate it with our hosts
    def create_unity_quicklist(self):
        entry = Unity.LauncherEntry.get_for_desktop_id("rocket-depot.desktop")
        self.quicklist = Dbusmenu.Menuitem.new()
        self.populate_unity_quicklist()
        entry.set_property("quicklist", self.quicklist)

    # Append a new host to the Unity quicklist
    def update_unity_quicklist(self, host):
        if host != 'DEFAULT':
            host_menu_item = Dbusmenu.Menuitem.new()
            host_menu_item.property_set(Dbusmenu.MENUITEM_PROP_LABEL,
                                        host)
            host_menu_item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE,
                                             True)
            host_menu_item.connect("item-activated", self.on_unity_clicked,
                                   host)
            self.quicklist.child_append(host_menu_item)

    # If we delete a host we must delete all Unity quicklist entries and
    # rebuild the quicklist
    def clean_unity_quicklist(self):
        for x in self.quicklist.get_children():
            self.quicklist.child_delete(x)
        self.populate_unity_quicklist()

    def start_thread(self):
        # Throw an error if the required host field is empty
        if not self.rd.options['host']:
            self.on_warn(None, 'No Host', 'No Host or IP Address Given')
        else:
            self.status_bar.push(0, 'Connecting to "' +
                                 self.rd.options['host'] + '" ...')
            self.host_combo.set_sensitive(False)
            self.userentry.set_sensitive(False)
            self.geometryentry.set_sensitive(False)
            self.clioptionsentry.set_sensitive(False)
            self.xfreerdpbutton.set_sensitive(False)
            self.rdesktopbutton.set_sensitive(False)
            self.homedirbutton.set_sensitive(False)
            self.grabkeyboardbutton.set_sensitive(False)
            self.fullscreenbutton.set_sensitive(False)
            self.terminalbutton.set_sensitive(False)
            self.connectbutton.set_sensitive(False)
            self.menubar.set_sensitive(False)
            self.spinner.start()
            cmdline = self.rd.run_program()
            # Print the command line that we constructed to the terminal
            if self.rd.debug:
                print '''Command to execute:
''' + ' '.join(str(x) for x in cmdline)
            thread = WorkerThread(self.work_finished_cb, cmdline)
            thread.start()

    # Triggered when a host is selected via the Unity quicklist
    def on_unity_clicked(self, widget, entry, host):
        self.rd.read_config(host)
        self.start_thread()

    # Trigged when we press 'Enter' or the 'Connect' button
    def enter_connect(self, *args):
        self.grab_textboxes()
        self.start_thread()

    def work_finished_cb(self):
        self.status_bar.pop(0)
        self.spinner.stop()
        self.host_combo.set_sensitive(True)
        self.userentry.set_sensitive(True)
        self.geometryentry.set_sensitive(True)
        self.clioptionsentry.set_sensitive(True)
        self.xfreerdpbutton.set_sensitive(True)
        self.rdesktopbutton.set_sensitive(True)
        self.homedirbutton.set_sensitive(True)
        self.grabkeyboardbutton.set_sensitive(True)
        self.fullscreenbutton.set_sensitive(True)
        self.terminalbutton.set_sensitive(True)
        self.connectbutton.set_sensitive(True)
        self.menubar.set_sensitive(True)
        error_text = WorkerThread.error_text
        return_code = WorkerThread.return_code
        return_code_ignore = [62, 255]
        # return code 62 is a benign error code from rdesktop
        # return code 62 is not used by xfreerdp
        # return code 255 is a benign error code from xfreerdp
        # return code 255 is not used by rdesktop
        if return_code is not 0 and return_code not in return_code_ignore:
            # discard extra data from long error messages
            if len(error_text) > 300:
                error_text = error_text[:300] + '...'
            self.on_warn(None, 'Connection Error', '%s: \n'
                         % self.rd.options['program'] + error_text)

    # Triggered when the combobox is clicked.  We load the selected host
    # from the config file.
    def on_host_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            name = model[tree_iter][0]
            for host in self.rd.saved_hosts:
                if name == host:
                    self.rd.read_config(name)
                    self.load_settings()
            self.rd.options['host'] = name
        else:
            entry = combo.get_child()
            text = entry.get_text()
            if text in self.rd.saved_hosts:
                self.rd.read_config(text)
                self.load_settings()
            else:
                self.rd.read_config('DEFAULT')
                self.load_settings()

    # Triggered when the checkboxes are toggled
    def on_button_toggled(self, button, name):
        if button.get_active():
            state = 'true'
            self.rd.options[name] = state
        else:
            state = 'false'
            self.rd.options[name] = state

    # Triggered when the program radio buttons are toggled
    def on_radio_button_toggled(self, button, name):
        if button.get_active():
            self.rd.options['program'] = name

    # Triggered when the file menu is used
    def add_file_menu_actions(self, action_group):
        action_filemenu = Gtk.Action(name="FileMenu", label="File",
                                     tooltip=None, stock_id=None)
        action_group.add_action(action_filemenu)
        # Why do the functions here execute on startup if we add parameters?
        action_group.add_actions([("SaveCurrentConfig", None,
                                   "Save Host", "<control>S", None,
                                   self.save_current_config)])
        action_group.add_actions([("SaveCurrentConfigAsDefault", None,
                                   "Save Settings as Default", "<control>D",
                                   None, self.save_current_config_as_default)])
        action_group.add_actions([("DeleteCurrentConfig", None,
                                   "Delete Host", "<control><shift>S", None,
                                   self.delete_current_config)])
        action_group.add_actions([("FileQuit", None,
                                   "Quit", "<control>Q", None,
                                   self.quit)])

    # Triggered when the help menu is used
    def add_help_menu_actions(self, action_group):
        action_group.add_actions([
            ("Help", None, "Help"),
            ("About", None, "About", None, None, self.on_menu_help_about),
            ("FreeRDPDocs", None, "FreeRDP Web Documentation", None, None,
             self.on_menu_xfreerdp_help),
            ("rdesktopDocs", None, "rdesktop Web Documentation", None, None,
             self.on_menu_rdesktop_help),
        ])

    # Needed for the menu bar
    def create_ui_manager(self):
        uimanager = Gtk.UIManager()
        # Throws exception if something went wrong
        uimanager.add_ui_from_string(self.UI_INFO)
        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    # When the save config button is clicked on the menu bar
    def save_current_config(self, widget):
        self.grab_textboxes()
        if (self.rd.options['host'] == '' or
                self.rd.options['host'] == 'DEFAULT'):
            self.on_warn(None, 'No hostname',
                         'Please name your host before saving.')
        else:
            self.rd.save_config(self.rd.options['host'])
            self.populate_host_combobox()
            self.status_bar.push(0, 'Host "' +
                                 self.rd.options['host'] + '" saved')
            if unity is True:
                self.clean_unity_quicklist()

    # When the delete config button is clicked on the menu bar
    def delete_current_config(self, widget):
        if (self.rd.options['host'] == '' or
                self.rd.options['host'] == 'DEFAULT'):
            self.on_warn(None, 'Select a Saved Host',
                         'Please select a saved host to delete.')
        else:
            self.rd.delete_config(self.rd.options['host'])
            # reload the default config
            self.rd.read_config('DEFAULT')
            self.load_settings()
            self.populate_host_combobox()
            self.host_entry.set_text('')
            if unity is True:
                self.clean_unity_quicklist()

    # When the save config button is clicked on the menu bar
    def save_current_config_as_default(self, widget):
        self.grab_textboxes()
        self.rd.save_config('DEFAULT')
        self.status_bar.push(0, 'Default host settings saved')

    # When the quit button is clicked on the menu bar
    def quit(self, widget):
        Gtk.main_quit()

    # When the help button is clicked on the menu bar
    def on_menu_help_about(self, widget):
        self.on_about(widget)

    # When the FreeRDP help button is clicked on the menu bar
    def on_menu_xfreerdp_help(self, widget):
        url = "https://github.com/FreeRDP/FreeRDP/wiki/CommandLineInterface"
        webbrowser.open_new_tab(url)

    # When the rdesktop help button is clicked on the menu bar
    def on_menu_rdesktop_help(self, widget):
        url = "http://linux.die.net/man/1/rdesktop"
        webbrowser.open_new_tab(url)

    # Grab all textbox input
    def grab_textboxes(self):
        self.rd.options['host'] = self.host_entry.get_text()
        self.rd.options['user'] = self.userentry.get_text()
        self.rd.options['geometry'] = self.geometryentry.get_text()
        self.rd.options['clioptions'] = self.clioptionsentry.get_text()

    # Generic warning dialog
    def on_warn(self, widget, title, message):
        dialog = Gtk.MessageDialog(transient_for=self, flags=0,
                                   message_type=Gtk.MessageType.WARNING,
                                   buttons=Gtk.ButtonsType.OK, text=title,
                                   title='Rocket Depot')
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    # About dialog
    def on_about(self, widget):
        about = Gtk.AboutDialog()
        about.set_program_name("Rocket Depot")
        about.set_version("0.24")
        about.set_copyright("2014 David Roble")
        about.set_comments("rdesktop/xfreerdp Frontend")
        about.set_website("https://github.com/robled/rocket-depot")
        about.set_logo(self.program_icon)
        about.set_icon(self.program_icon)
        about.run()
        about.destroy()

    # Load all settings
    def load_settings(self):
        self.userentry.set_text(self.rd.options['user'])
        self.geometryentry.set_text(self.rd.options['geometry'])
        self.clioptionsentry.set_text(self.rd.options['clioptions'])
        if self.rd.options['program'] == 'xfreerdp':
            self.xfreerdpbutton.set_active(True)
        if self.rd.options['program'] == 'rdesktop':
            self.rdesktopbutton.set_active(True)
        if self.rd.options['homeshare'] == 'true':
            self.homedirbutton.set_active(True)
        else:
            self.homedirbutton.set_active(False)
        if self.rd.options['grabkeyboard'] == 'true':
            self.grabkeyboardbutton.set_active(True)
        else:
            self.grabkeyboardbutton.set_active(False)
        if self.rd.options['fullscreen'] == 'true':
            self.fullscreenbutton.set_active(True)
        else:
            self.fullscreenbutton.set_active(False)
        if self.rd.options['terminal'] == 'true':
            self.terminalbutton.set_active(True)
        else:
            self.terminalbutton.set_active(False)
        self.status_bar_load_host()

    def status_bar_load_host(self):
        if (self.rd.options['host'] == '' or
                self.rd.options['host'] == 'DEFAULT'):
            self.status_bar.push(0, 'Default host settings loaded')
        else:
            self.status_bar.push(0, 'Saved host "' +
                                 self.rd.options['host'] + '" loaded')


def _main():
    rocket_depot = RocketDepot()
    window = MainWindow(rocket_depot)
    window.connect("delete-event", Gtk.main_quit)
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    _main()
