import subprocess
from distutils.log import warn, info
from setuptools import setup

setup(
    name='rocket-depot',
    version='1.0.0',
    scripts=['rocket-depot'],

    # metadata for upload to PyPI
    platforms='linux',
    author='David Roble',
    author_email='robled@electronsweatshop.com',
    maintainer='David Roble',
    maintainer_email='robled@electronsweatshop.com',
    description='An rdesktop/xfreerdp frontend.',
    long_description=open('README.txt').read(),
    license='GNU GPLv3',
    keywords=['rdesktop', 'freerdp', 'rdp', 'remote desktop',
              'terminal server'],
    url='https://github.com/robled/rocket-depot',
    data_files=[
        ('/usr/share/applications',
            ['data/rocket-depot.desktop']),
        ('/usr/share/icons/hicolor/16x16/apps',
            ['data/icons/16x16/apps/rocket-depot.png']),
        ('/usr/share/icons/hicolor/22x22/apps',
            ['data/icons/22x22/apps/rocket-depot.png']),
        ('/usr/share/icons/hicolor/24x24/apps',
            ['data/icons/24x24/apps/rocket-depot.png']),
        ('/usr/share/icons/hicolor/32x32/apps',
            ['data/icons/32x32/apps/rocket-depot.png']),
        ('/usr/share/icons/hicolor/48x48/apps',
            ['data/icons/48x48/apps/rocket-depot.png']),
        ('/usr/share/icons/hicolor/64x64/apps',
            ['data/icons/64x64/apps/rocket-depot.png']),
        ('/usr/share/icons/hicolor/128x128/apps',
            ['data/icons/128x128/apps/rocket-depot.png']),
        ('/usr/share/icons/hicolor/256x256/apps',
            ['data/icons/256x256/apps/rocket-depot.png']),
        ('/usr/share/icons/hicolor/scalable/apps',
            ['data/icons/scalable/apps/rocket-depot.svg']),
        ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
        ],
)

info('running gtk-update-icon-cache')
try:
    subprocess.call(['gtk-update-icon-cache', '-q', '-f', '-t',
                     '/usr/share/icons/hicolor'])
except OSError as e:
    warn('updating the GTK icon cache failed: %s' % str(e))
