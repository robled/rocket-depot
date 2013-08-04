#!/usr/bin/python

# Originally written by Cory Wright
# http://projects.standblue.net/software/#rdesktop-open

import os
import string
from gi.repository import Gtk, Gdk, GObject
from gi.repository.GdkPixbuf import Pixbuf

if os.environ.has_key('USER'):
    user = os.environ['USER']
else:
    user = 'username'

configfile = '%s/.rdesktop-opener' % os.environ['HOME']

options = {'host'          : 'host.example.com',
           'user'          : 'user',
           'resolution'    : '1024x768',
           'program'       : 'rdesktop',
           'homeshare'     : 0,
           'grabkeyboard'  : 0,
           'fullscreen'    : 0
            }

optlist = ('host',
           'user',
           'resolution',
           'program',
           'homeshare',
           'grabkeyboard',
           'fullscreen'
           )

def save_conf():
    # host, user name, resolution, program (rdesktop,xfreerdp), fullscreen
    # (0,1), grab keyboard (0,1), homeshare (0,1)
    conf = open(configfile, 'w')
    host = options['host']
    user = options['user']
    geometry = options['resolution']
    program = options['program']
    try:
        if options['host'] != string.strip(window.hostentry.get_text()):
            host = string.strip(window.hostentry.get_text())
        if options['user'] != string.strip(window.userentry.get_text()):
            user = string.strip(window.userentry.get_text())
        if options['resolution'] != string.strip(window.geometryentry.get_text()):
            geometry = string.strip(window.geometryentry.get_text())
        if options['program'] != selprogram:
            program = selprogram
    except:
        pass
    #ofline = '%s,%s,%s,%s,' % (window.hostentry.get_text(), window.userentry.get_text(), geometry,
    #                           selprogram)
    ofline = '%s,%s,%s,%s,' % (host, user, geometry, program)
    ofline = ofline + '%s,%s,%s\n' % (
        options['homeshare'], options['grabkeyboard'], options['fullscreen'])
    conf.write(ofline)
    conf.close()

try:
    conf = open(configfile, 'r')
except IOError:
    save_conf()
else:
    if conf:
        readconf = string.strip(conf.readline())
        # host, user name, resolution, program (rdesktop,xfreerdp), fullscreen
        # (0,1), grab keyboard (0,1), homeshare (0,1)
        optindex = 0
        for opt in string.split(readconf, ','):
            options[optlist[optindex]] = opt
            optindex = optindex + 1

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

class MainWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="rdesktop-opener", resizable=0)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(8)
        progicon = Gtk.IconTheme.get_default().load_icon('gnome-network-properties', 64, 0)
        self.set_icon(progicon)

        program_store = Gtk.ListStore(str)
        programs = {'rdesktop':1, 'xfreerdp':0}
        for key in programs:
            program_store.append([key])

        program_combo = Gtk.ComboBox.new_with_model(program_store)
        program_combo.connect("changed", self.on_program_combo_changed)
        renderer_text = Gtk.CellRendererText()
        program_combo.pack_start(renderer_text, True)
        program_combo.add_attribute(renderer_text, "text", 0)
        program_combo.set_active(programs[options['program']])

        action_group = Gtk.ActionGroup("Menu")

        self.add_file_menu_actions(action_group)
        self.add_options_menu_actions(action_group)
        self.add_help_menu_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")

        quitbutton = Gtk.Button(label="Quit")
        quitbutton.connect("clicked", self.on_menu_file_quit)

        connectbutton = Gtk.Button(label="Connect")
        connectbutton.connect("clicked", self.on_connectbutton_clicked)

        homedirbutton = Gtk.CheckButton("Share Home Dir")
        homedirbutton.connect("toggled", self.on_button_toggled, "homeshare")
        if options['homeshare'] == '1':
            homedirbutton.set_active(True)

        grabkeyboardbutton = Gtk.CheckButton("Grab Keyboard")
        grabkeyboardbutton.connect("toggled", self.on_button_toggled, "grabkeyboard")
        if options['grabkeyboard'] == '1':
            grabkeyboardbutton.set_active(True)

        fullscreenbutton = Gtk.CheckButton("Fullscreen")
        fullscreenbutton.connect("toggled", self.on_button_toggled, "fullscreen")
        if options['fullscreen'] == '1':
            fullscreenbutton.set_active(True)

        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        self.add(grid)

        hostlabel = Gtk.Label("Host")
        userlabel = Gtk.Label("Username")
        geometrylabel = Gtk.Label("Geometry")
        programlabel = Gtk.Label("Program")

        self.hostentry = Gtk.Entry()
        self.hostentry.set_text(options['host'])
        self.hostentry.connect("activate", self.enter_callback, self.hostentry)
        self.userentry = Gtk.Entry()
        self.userentry.set_text(options['user'])
        self.userentry.connect("activate", self.enter_callback, self.userentry)
        self.geometryentry = Gtk.Entry()
        self.geometryentry.set_text(options['resolution'])
        self.geometryentry.connect("activate", self.enter_callback, self.geometryentry)

        grid.attach(menubar, 0, 0, 12, 4)
        grid.attach(hostlabel, 0, 4, 4, 4)
        grid.attach(userlabel, 0, 8, 4, 4)
        grid.attach(geometrylabel, 0, 16, 4, 4)
        grid.attach(programlabel, 0, 20, 4, 4)
        grid.attach_next_to(self.hostentry, hostlabel, Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.userentry, userlabel, Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(self.geometryentry, geometrylabel, Gtk.PositionType.RIGHT, 8, 4)
        grid.attach_next_to(program_combo, programlabel, Gtk.PositionType.RIGHT, 8, 4)
        grid.attach(homedirbutton, 0, 24, 4, 4)
        grid.attach_next_to(grabkeyboardbutton, homedirbutton, Gtk.PositionType.RIGHT, 4, 4)
        grid.attach_next_to(fullscreenbutton, grabkeyboardbutton, Gtk.PositionType.RIGHT, 4, 4)
        grid.attach(quitbutton, 0, 28, 4, 4)
        grid.attach_next_to(connectbutton, quitbutton, Gtk.PositionType.RIGHT, 8, 4)

    def enter_callback(self, widget, entry):
        options['host'] = self.hostentry.get_text()
        options['user'] = self.userentry.get_text()
        options['resolution'] = self.geometryentry.get_text()
        run_rdesktop()

    def on_program_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            program = model[tree_iter][0]
        global selprogram
        selprogram = program

    def on_button_toggled(self, button, name):
        if button.get_active():
            state = 1
            options[name] = state
        else:
            state = 0
            options[name] = state

    def on_connectbutton_clicked(self, widget):
        run_rdesktop()

    def add_file_menu_actions(self, action_group):
        action_filemenu = Gtk.Action("FileMenu", "File", None, None)
        action_group.add_action(action_filemenu)

        action_group.add_actions([
            ("SaveCurrentConfig", None, "Save Current Configuration", None, None,
             self.on_menu_file_save_config),
        ])

        action_filequit = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.on_menu_file_quit)
        action_group.add_action(action_filequit)

    def add_options_menu_actions(self, action_group):
        action_group.add_actions([
            ("OptionMenu", None, "Options"),
            ("PrintDebug", None, "Print Debugging to Terminal", None, None,
             self.on_menu_debug),
        ])

    def add_help_menu_actions(self, action_group):
        action_group.add_actions([
            ("Help", None, "Help"),
            ("About", None, "About", None, None,
             self.on_menu_help),
        ])

    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    def on_menu_file_save_config(self, widget):
        save_conf()

    def on_menu_file_quit(self, widget):
        Gtk.main_quit()

    def on_menu_help(self, widget):
        self.on_about(widget)

    def on_menu_debug(self, widget):
        print_options()

    def on_info(self, widget):
        # TODO: let's try and set the title and icon later
        #Gtk.Window(title="MessageDialog")
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, "This is an INFO MessageDialog")
        dialog.set_title("hi")
        dialog.format_secondary_text(
            "And this is the secondary text that explains things.")
        dialog.run()

        dialog.destroy()

    def on_warn(self, widget, title, message):
        Gtk.Window(title="what")
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
            Gtk.ButtonsType.OK, title)
        dialog.format_secondary_text(message)
        response = dialog.run()
        dialog.destroy()

    def on_about(self, widget):
        about = Gtk.AboutDialog()
        about.set_program_name("rdesktop-opener")
        about.set_version("0.0")
        #about.set_copyright("(c) aperson")
        about.set_comments("rdesktop/xfreerdp Frontend")
        about.set_website("https://github.com/robled/rdesktop-opener")
        about.run()
        about.destroy()

window = MainWindow()


def run_rdesktop():
    client_opts = {
        'rdesktop': {
            'stdopts': ['rdesktop', '-k', 'en-us', '-a', '16'],
            'host': '',
            'user': '-u',
            'resolution': '-g',
            'homeshare': '-rdisk:home=' + os.environ['HOME'],
            'grabkeyboard': '-K',
            'fullscreen': '-f'
        },
        'xfreerdp': {
            'stdopts': ['xfreerdp', '/cert-ignore', '-sec-nla', '+clipboard'],
            'host': '/v:',
            'user': '/u:',
            'resolution': '/size:',
            'homeshare': '+home-drive',
            'grabkeyboard': '-grab-keyboard',
            'fullscreen': '/f'
        }
    }

    client = selprogram 
    params = []
    for x in client_opts[client]['stdopts']:
        params.append(x)

    if options['host'] == '':
        window.on_warn('null', 'No Host', 'No Host or IP Address Given')
        return
    if options['user'] != '':
        params.append(client_opts[client]['user'] + '%s' % string.strip(options['user']))
    if options['resolution'] != '':
        params.append(client_opts[client]['resolution'] + '%s' % string.strip(options['resolution']))
    if options['fullscreen'] == 1:
        params.append(client_opts[client]['fullscreen'])
    if options['grabkeyboard'] == '0':
        params.append(client_opts[client]['grabkeyboard'])
    if options['homeshare'] == 1:
        params.append(client_opts[client]['homeshare'])
    if options['host']:
        params.append(client_opts[client]['host'] + '%s' % string.strip(options['host']))

    print params
    os.spawnvp(os.P_NOWAIT, params[0], params)
    return

def print_options():
    print '-- currently selected options --'
    print 'host => ' + options['host']
    print 'user => ' + options['user']
    print 'resolution => ' + options['resolution']
    print 'program => ' + selprogram 
    print 'homeshare => ' + str(options['homeshare']) 
    print 'grabkeyboard => ' + str(options['grabkeyboard']) 
    print 'fullscreen => ' + str(options['fullscreen'])

window.connect("delete-event", Gtk.main_quit)
window.show_all()
Gtk.main()
