# Copyright (C) 2008, Vincent Povirk for CodeWeavers
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from sugar.activity import activity
import sys
import os
import gobject
import gtk
import shutil
import tempfile
import logging
import atexit

class WineActivity(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.bundle_path = activity.get_bundle_path()

        try:
            activity_root = activity.get_activity_root()
            wine_prefix = os.path.join(activity_root, 'data', 'wine')
        except AttributeError:
            try:
                activity_root = os.environ['SUGAR_ACTIVITY_ROOT']
                wine_prefix = os.path.join(activity_root, 'data', 'wine')
            except KeyError:
                activity_root = None
                wine_prefix = os.path.expanduser('~/.wine')
        
        self.settings = {}
        f = open(os.path.join(self.bundle_path, 'activity', 'wine.info'), 'U')
        for line in f.readlines():
            if '=' in line:
                key, value = line.rstrip('\n').split('=')
                self.settings[key] = value
        f.close()
        
        try:
            self.desktop_parent = gtk.EventBox()
            self.desktop_parent.show()
            self.set_canvas(self.desktop_parent)
        except AttributeError:
            # remove any children of the window that Sugar may have added
            for widget in self.get_children():
                self.remove(widget)

            self.desktop_parent = self
        
        os.environ['LD_LIBRARY_PATH'] = "%s:%s" % (os.path.join(self.bundle_path, 'lib'), os.environ.get('LD_LIBRARY_PATH', ''))
        os.environ['PATH'] = "%s:%s" % (os.path.join(self.bundle_path, 'bin'), os.environ.get('PATH', ''))
        os.environ['WINEPREFIX'] = wine_prefix
        os.environ['WINELOADER'] = os.path.join(self.bundle_path, 'bin/wine')
        os.environ['WINESERVER'] = os.path.join(self.bundle_path, 'bin/wineserver')
        os.environ['WINEDLLPATH'] = os.path.join(self.bundle_path, 'lib/wine')
        
        self.desktop_name = str(os.getpid())
        os.environ['WINE_DESKTOP_NAME'] = self.desktop_name
        
        firstrun = not os.path.exists(wine_prefix)
        
        self.setup_prefix(firstrun)

        self.desktop_parent.connect('map', self.on_parent_map)
        
        self.wine_pid = None
        
        self.to_run = []
        self.tempfiles = []

        self.set_title("Wine")
    
    def on_parent_map(self, widget):
        os.environ['WINE_DESKTOP_PARENT'] = str(self.desktop_parent.window.xid)
        os.environ['SUGARED_WINE_TOPLEVEL'] = str(self.window.xid)

        gtk.gdk.flush()

        os.chdir(self.get_unix_path('c:\\'))

        width = gtk.gdk.screen_width()
        height = gtk.gdk.screen_height()

        cmdline = ('wine', 'explorer', '/desktop=%s,%sx%s' % (self.desktop_name, width, height))
        try:
            args = self.settings['exec'].split(' ')
        except KeyError:
            pass
        else:
            cmdline += ('start', '/unix')
            cmdline += (os.path.join(self.bundle_path, args[0]),)
            cmdline += tuple(args[1:])

        self.wine_pid, stdin, stdout, stderr = gobject.spawn_async(cmdline,
            flags=gobject.SPAWN_SEARCH_PATH|gobject.SPAWN_DO_NOT_REAP_CHILD)
        gobject.child_watch_add(self.wine_pid, self.on_wine_quit, None)
        
        for cmdline in self.to_run:
            self.start_wine(*cmdline)
    
    def start_wine(self, *args):
        if self.wine_pid:
            logging.info("running command line: %s" % ' '.join(str(x) for x in args))
            gobject.spawn_async(
                ['wine', 'explorer', '/desktop=%s' % self.desktop_name] + [str(x) for x in args],
                flags=gobject.SPAWN_SEARCH_PATH)
        else:
            self.to_run.append(args)
    
    def run_cmd(self, *args):
        pid, stdin, stdout, stderr = gobject.spawn_async(
            args,
            flags=gobject.SPAWN_SEARCH_PATH,
            standard_output=True)
        
        result = []
        s = os.read(stdout, 4096)
        while s:
            result.append(s)
            s = os.read(stdout, 4096)
        
        result = ''.join(result)
        
        return result
        
    def get_unix_path(self, windowspath):
        return self.run_cmd('winepath', '--unix', windowspath).rstrip('\n')

    def setup_prefix(self, firstrun):
        try:
            f = open(os.path.join(os.environ['WINEPREFIX'], '.update-timestamp'), 'r')
            try:
                timestamp = int(f.read().strip())
            finally:
                f.close()
            
            expected_timestamp = os.stat(os.path.join(self.bundle_path, 'share/wine/wine.inf')).st_mtime
            if timestamp == expected_timestamp:
                #no update needed
                return
        except IOError:
            pass
        
        try:
            self.run_cmd('wine', 'start', '/unix', os.path.join(self.bundle_path, self.settings['init']))
        except KeyError:
            self.run_cmd('wineboot', '--update')

        self.run_cmd('wineserver', '-w')

        if firstrun:
            try:
                background_file = os.path.join(self.bundle_path, self.settings['background'])
            except KeyError:
                pass
            else:
                #set up desktop background
                winini = self.get_unix_path(r'c:\windows\win.ini')
                
                f = open(winini, 'w')
                f.write("\r\n\r\n[desktop]\r\nWallPaper=c:\\windows\\background.bmp")
                f.close()
                
                landscapebmp = self.get_unix_path(r'c:\windows\background.bmp')
                os.symlink(background_file, landscapebmp)
    
    def on_wine_quit(self, pid, condition, data):
        sys.exit()
    
    def read_file(self, file_path):
        #the file is read-only and will be deleted so make a copy
        import filenames
        fd, filename = filenames.create_dsobject_file(self.metadata)
        os.chmod(filename, int('0770', 8))
        shutil.copyfile(file_path, filename)
        os.close(fd)
        atexit.register(os.unlink, filename)
        self.start_wine('start', '/unix', filename)

