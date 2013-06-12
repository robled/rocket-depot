#!/usr/bin/python2

# rdp-start.py Cory Wright, Public Domain Software
# $Id: rdesktop-open.py,v 1.6 2003/02/04 19:34:07 cwright Exp $

from Tkinter import *
import os, string

if os.environ.has_key('USER'):
    user = os.environ['USER']
else:
    user = "username"

options = { "host"       : "host.example.com",
            "user"       : user,
            "resolution" : "85%",
            "pass"       : "",
            "domain"     : "",
            "fullscreen" : 0,
            "grabkeyboard"    : 0 }

optlist = ("host","user","resolution","domain","fullscreen","grabkeyboard")

screens = ['85%', '1280x800', '1600x900']
screenl = ['85%', '1280 X 800', '1600 X 900']

configfile = "%s/.rdesktop-open" % os.environ['HOME']

def popup_alert(title,textmsg):
    alert = Tk()
    alert.title("Notice: "+title)
    Label(alert,text="Notice: "+textmsg).pack()
    alert.mainloop()

def save_conf():
    # host, user name, resolution, domain, fullscreen (0,1), grab keyboard (0,1)
    conf = open(configfile,"w")
    try:
        saveres = string.atoi(listbox.curselection()[0])
    except IndexError:
        saveres = 0
    screen = screens[saveres]
    ofline = "%s,%s,%s,," % (textHost.get(),textUsername.get(),screen)
    ofline = ofline + "%s,%s\n" % (varFs.get(),varGrabKeyboard.get())
    conf.write(ofline)
    conf.close()

def open_url(url):
    os.spawnvp("P_NOWAIT","mozilla",('mozilla',url))
    return

def open_rdesktop_site():
    open_url("http://www.rdesktop.org/")
    return

def open_rdo_site():
    open_url("http://projects.standblue.net/software/")
    return

def run_rdesktop():
    params = ['rdesktop']

    if(textHost.get() == ""):
        popup_alert("No Host","No Host or IP Address Given")
        return
    if(textUsername.get() != ""):
        params.append("-u")
        params.append("%s" % string.strip(textUsername.get()))
    if(textPassword.get() != ""):
        params.append("-p")
        params.append("%s" % string.strip(textPassword.get()))
    try:
        screenIndex = string.atoi(listbox.curselection()[0])
    except IndexError:
        screen = screens[0]
    else:
        screen = screens[screenIndex]
    if(screen != ""):
        params.append("-g")
        params.append("%s" % screen)
    if(varFs.get() == 1):
        params.append("-f")
    if(varGrabKeyboard.get() == 0):
        params.append("-K")
    if(textHost.get() != ""):
        params.append("%s" % string.strip(textHost.get()))

    print params
    os.spawnvp(os.P_NOWAIT, params[0], params)
    return

def print_options():
    print "-- default options --"
    for i in options.keys():
        print i, " => ", options[i]
    print "-- currently selected options --"
    print "host => " + textHost.get()
    print "user => " + textUsername.get()
    print "resolution => " + screens[string.atoi(listbox.curselection()[0])]
    print "pass => " + textPassword.get()
    print "domain => "
    print "fullscreen => " + str(varFs.get())
    print "grabkeyboard => " + str(varGrabKeyboard.get())

try:
    conf = open(configfile,"r")
except IOError:
    popup_alert("No ~/.rdesktop-open found",
                "No ~/.rdesktop-open file was found.\nChoose 'Save' from the 'File' menu to create one")
else:
    if(conf):
        readconf = string.strip(conf.readline())
        # host, user name, resolution, domain, fullscreen (0,1), grab keyboard (0,1)
        optindex = 0
        for opt in string.split(readconf,","):
            options[optlist[optindex]] = opt
            optindex = optindex + 1

if __name__ == "__main__":

    root = Tk()
    root.title("rdesktop-open.py: RDesktop Frontend")

    menuFrameTop = Frame(root,relief=RIDGE,bd=2)
    menuFrameTop.pack(side=TOP,fill=X)

    menuFileButton = Menubutton(menuFrameTop,text='File',underline=0)
    menuFileButton.pack(side=LEFT)
    menuFileDropdown = Menu(menuFileButton,relief=RIDGE)
    menuFileDropdown.add_command(label="Save Current Configuration",underline=0,command=save_conf)
    menuFileDropdown.add_command(label="Exit",underline=0,command=root.destroy)
    menuFileButton.config(menu=menuFileDropdown)

    menuOptsButton = Menubutton(menuFrameTop,text='Options',underline=0)
    menuOptsButton.pack(side=LEFT)
    menuOptsDropdown = Menu(menuOptsButton,relief=RIDGE)
    menuOptsDropdown.add_command(label="Print Debugging Info To Console",underline=0,command=print_options)
    menuOptsButton.config(menu=menuOptsDropdown)

    menuHelpButton = Menubutton(menuFrameTop,text='Help',underline=0)
    menuHelpButton.pack(side=RIGHT)
    menuHelpDropdown = Menu(menuHelpButton,relief=RIDGE)
    menuHelpDropdown.add_command(label="RDesktop Homepage",underline=0,command=open_rdesktop_site)
    menuHelpDropdown.add_command(label="rdesktop-open Homepage",underline=9,command=open_rdo_site)
    menuHelpButton.config(menu=menuHelpDropdown)

    # Create the area for hosts
    frameHost = Frame(root)
    labelHost = Label(frameHost,width=9,text='Host')
    textHost = Entry(frameHost)
    textHost.insert(0,options['host'])
    frameHost.pack(side=TOP, fill=X)
    labelHost.pack(side=LEFT)
    textHost.pack(side=RIGHT, expand=YES, fill=X)
    textHost.focus()
    textHost.bind('<Return>', (lambda event: run_rdesktop()))

    # Create the area for user name
    frameUsername = Frame(root)
    labelUsername = Label(frameUsername,width=9,text='Username')
    textUsername = Entry(frameUsername)
    textUsername.insert(0,options['user'])
    frameUsername.pack(side=TOP, fill=X)
    labelUsername.pack(side=LEFT)
    textUsername.pack(side=RIGHT, expand=YES, fill=X)

    # Create the area for the password
    framePassword = Frame(root)
    labelPassword = Label(framePassword,width=9,text='Password')
    textPassword = Entry(framePassword, show='**')
    textPassword.insert(0,options['pass'])
    framePassword.pack(side=TOP, fill=X)
    labelPassword.pack(side=LEFT)
    textPassword.pack(side=RIGHT, expand=YES, fill=X)

    # Create the area for the full screen
    rightFrame = Frame(root)
    varFs = IntVar()
    varFs.set(options['fullscreen'])
    Checkbutton(rightFrame, text='Fullscreen', variable=varFs).pack(side=RIGHT, expand=YES, fill=X)
    varGrabKeyboard = IntVar()
    varGrabKeyboard.set(options['grabkeyboard'])
    Checkbutton(rightFrame, text='Grab keyboard', variable=varGrabKeyboard).pack(side=RIGHT, expand=YES, fill=X)
    rightFrame.pack(side=TOP)

    # Create the area and the scrolldown for resolution
    frameResolution = Frame(root)
    labelResolution = Label(frameResolution,width=9,text='Screen')
    selectResolution = Listbox(frameResolution, relief=RIDGE, height=3)

    tcount = 0
    defres = 0
    for size in screenl:
        if screens[tcount] == options['resolution']:
            defres = tcount
        selectResolution.insert('end',size)
        tcount = tcount + 1

    selectResolution.select_set(defres)
    listbox = selectResolution

    frameResolution.pack(side=TOP, fill=X)
    labelResolution.pack(side=LEFT)
    selectResolution.pack(side=LEFT, fill=Y)

    frameButtons = Frame(root)
    frameButtons.pack(side=BOTTOM)
    Button(frameButtons,text="Quit",command=root.destroy).pack(side=LEFT, fill=X)
    Button(frameButtons,text='Connect',command=run_rdesktop).pack(side=RIGHT, fill=X)

    root.mainloop()

print "rdesktop-open.py -- http://projects.standblue.net/software/"
print "Cory Wright, Stand Blue Technology -- $Date: 2003/02/04 19:34:07 $"
