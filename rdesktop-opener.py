#!/usr/bin/env python

# Originally written by Cory Wright
# http://projects.standblue.net/software/#rdesktop-open

import os
import string
from Tkinter import *

if os.environ.has_key('USER'):
    user = os.environ['USER']
else:
    user = 'username'

options = {'host'          : 'host.example.com',
           'user'          : 'user',
           'resolution'    : '1024x768',
           'program'       : 'rdesktop',
           'pass'          : '',
           'fullscreen'    : 0,
           'grabkeyboard'  : 0,
           'homeshare'     : 0,
            }

optlist = ('host',
           'user',
           'resolution',
           'program',
           'fullscreen',
           'grabkeyboard',
           'homeshare'
           )

configfile = '%s/.rdesktop-opener' % os.environ['HOME']

def popup_alert(title, textmsg):
    alert = Tk(className='rdesktop-opener')
    alert.title('Notice: '+title)
    Label(alert, text='Notice: '+textmsg).pack()
    alert.mainloop()

def save_conf():
    # host, user name, resolution, program (rdesktop,xfreerdp), fullscreen
    # (0,1), grab keyboard (0,1), homeshare (0,1)
    conf = open(configfile, 'w')
    geometry = string.strip(textGeometry.get())
    ofline = '%s,%s,%s,%s,' % (textHost.get(), textUsername.get(), geometry,
                               varProgram.get())
    ofline = ofline + '%s,%s,%s\n' % (
        varFs.get(), varGrabKeyboard.get(), varHomeShare.get())
    conf.write(ofline)
    conf.close()

def open_url(url):
    os.spawnvp('P_NOWAIT', 'x-www-browser',('x-www-browser' ,url))
    return

def open_rdesktop_site():
    open_url('http://www.rdesktop.org/')
    return

def open_rdo_site():
    open_url('http://projects.standblue.net/software/')
    return

def open_rdoer_site():
    open_url('https://github.com/robled/rdesktop-opener/')
    return

def run_rdesktop():
    client = varProgram.get()
    if client == 'rdesktop':
        params = ['rdesktop', '-k', 'en-us', '-a', '16']
    else:
        params = ['xfreerdp', '/cert-ignore', '-sec-nla', '+clipboard']

    if textHost.get() == '':
        popup_alert('No Host', 'No Host or IP Address Given')
        return
    if textUsername.get() != '':
        if client == 'rdesktop':
            params.append('-u')
            params.append('%s' % string.strip(textUsername.get()))
        else:
            params.append('/u:' + '%s' % string.strip(textUsername.get()))
    if textPassword.get() != '':
        if client == 'rdesktop':
            params.append('-p')
            params.append('%s' % string.strip(textPassword.get()))
        else:
            params.append('/p:' + '%s' % string.strip(textPassword.get()))
    if textGeometry.get() != '':
        if client == 'rdesktop':
            params.append('-g')
            params.append('%s' % string.strip(textGeometry.get()))
        else:
            params.append('/size:' + '%s' % string.strip(textGeometry.get()))
    if varFs.get() == 1:
        if client == 'rdesktop':
            params.append('-f')
        else:
            params.append('/f')
    if varGrabKeyboard.get() == 0:
        if client == 'rdesktop':
            params.append('-K')
        else:
            params.append('-grab-keyboard')
    if varHomeShare.get() == 1:
        if client == 'rdesktop':
            params.append('-r')
            params.append('disk:home=' + os.environ['HOME'])
        else:
            params.append('+home-drive')
    if textHost.get() != '':
        if client == 'rdesktop':
            params.append('%s' % string.strip(textHost.get()))
        else:
            params.append('/v:' + '%s' % string.strip(textHost.get()))

    os.spawnvp(os.P_NOWAIT, params[0], params)
    return

def print_options():
    print '-- default options --'
    for i in options.keys():
        print i, ' => ', options[i]
    print '-- currently selected options --'
    print 'host => ' + textHost.get()
    print 'user => ' + textUsername.get()
    print 'resolution => ' + textGeometry.get()
    print 'program => ' + str(varProgram.get())
    print 'fullscreen => ' + str(varFs.get())
    print 'grabkeyboard => ' + str(varGrabKeyboard.get())
    print 'homeshare => ' + str(varHomeShare.get())

try:
    conf = open(configfile, 'r')
except IOError:
    popup_alert(
        'No ~/.rdesktop-opener found',
    '''No ~/.rdesktop-opener file was found.\n
    Choose 'Save' from the 'File' menu to create one.''')
else:
    if conf:
        readconf = string.strip(conf.readline())
        # host, user name, resolution, program (rdesktop,xfreerdp), fullscreen
        # (0,1), grab keyboard (0,1), homeshare (0,1)
        optindex = 0
        for opt in string.split(readconf, ','):
            options[optlist[optindex]] = opt
            optindex = optindex + 1

if __name__ == '__main__':

    root = Tk(className='rdesktop-opener')
    root.title('rdesktop-opener')

    menuFrameTop = Frame(root, relief=RIDGE, bd=2)
    menuFrameTop.pack(side=TOP, fill=X)

    # Standard application menu
    def fmenubutton(label, packside, actionlabel, action):
        menubutton = Menubutton(menuFrameTop, text=label, underline=0)
        menubutton.pack(side=packside)
        menuFileDropdown = Menu(menubutton, relief=RIDGE)
        menubutton.config(menu=menuFileDropdown)
        index = 0
        for x in actionlabel:
            menuFileDropdown.add_command(label=actionlabel[index], underline=0,
                                         command=action[index])
            index += 1

    # Our application menu options
    fmenubutton('File', LEFT, ['Save Current Configuration', 'Exit'],
                [save_conf, root.destroy])
    fmenubutton('Options', LEFT, ['Print Debugging Info To Console'],
                [print_options])
    fmenubutton('Help', RIGHT, ['RDesktop Homepage', 'rdesktop-open Homepage',
                'rdesktop-opener GitHub'], [open_rdesktop_site, open_rdo_site,
                open_rdoer_site])

    # Create the area for hosts
    frameHost = Frame(root)
    labelHost = Label(frameHost, width=9, text='Host')
    textHost = Entry(frameHost)
    textHost.insert(0, options['host'])
    frameHost.pack(side=TOP, fill=X)
    labelHost.pack(side=LEFT)
    textHost.pack(side=RIGHT, expand=YES, fill=X)
    textHost.focus()
    textHost.bind('<Return>', (lambda event: run_rdesktop()))

    # Create the area for user name
    frameUsername = Frame(root)
    labelUsername = Label(frameUsername, width=9, text='Username')
    textUsername = Entry(frameUsername)
    textUsername.insert(0, options['user'])
    frameUsername.pack(side=TOP, fill=X)
    labelUsername.pack(side=LEFT)
    textUsername.pack(side=RIGHT, expand=YES, fill=X)

    # Create the area for the password
    framePassword = Frame(root)
    labelPassword = Label(framePassword, width=9, text='Password')
    textPassword = Entry(framePassword, show='**')
    textPassword.insert(0, options['pass'])
    framePassword.pack(side=TOP, fill=X)
    labelPassword.pack(side=LEFT)
    textPassword.pack(side=RIGHT, expand=YES, fill=X)

    # Create the area for geometry
    frameGeometry = Frame(root)
    labelGeometry = Label(frameGeometry, width=9, text='Geometry')
    textGeometry = Entry(frameGeometry, width=9)
    textGeometry.insert(0, options['resolution'])
    frameGeometry.pack(side=TOP, fill=X)
    labelGeometry.pack(side=LEFT)
    textGeometry.pack(side=LEFT, expand=NO)

    # Create the area for the program
    frameProgram = Frame(root)
    labelProgram = Label(frameProgram, width=9, text='Program')
    frameProgram.pack(side=TOP, fill=X)
    labelProgram.pack(side=LEFT)
    programList=['rdesktop','xfreerdp']
    varProgram = StringVar(root)
    varProgram.set(options['program'])
    programMenu=OptionMenu(frameProgram, varProgram, *programList)
    programMenu.pack(side=LEFT)
    programMenu.config(width=8)

    # Create the area for the checkboxes
    rightFrame = Frame(root)

    # Generic checkboxes
    def checkbox(checkvar, option, label, pack):
        checkvar.set(options[option])
        Checkbutton(
            rightFrame, text=label,
            variable=checkvar).pack(side=pack, expand=YES, fill=X)
        rightFrame.pack(side=TOP)

    varFs = IntVar()
    varGrabKeyboard = IntVar()
    varHomeShare = IntVar()
    checkbox(varHomeShare, 'homeshare', 'Share Home Dir', LEFT)
    checkbox(varGrabKeyboard, 'grabkeyboard', 'Grab Keyboard', LEFT)
    checkbox(varFs, 'fullscreen', 'Fullscreen', RIGHT)

    # Create the area for the connect/quit buttons
    frameButtons = Frame(root)
    frameButtons.pack(side=BOTTOM)
    Button(
        frameButtons, text='Quit', command=root.destroy).pack(side=LEFT,
        fill=X)
    Button(
        frameButtons, text='Connect', command=run_rdesktop).pack(side=RIGHT,
        fill=X)

    root.mainloop()

print 'rdesktop-opener.py -- https://github.com/robled/rdesktop-opener'
