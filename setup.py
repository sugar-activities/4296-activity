#!/usr/bin/env python
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

try:
    from sugar.activity import bundlebuilder
    bundlebuilder.start()
except ImportError:
    import os

    info = {}
    f = open(os.path.join('activity', 'activity.info'), 'U')
    for line in f.readlines():
        if '=' in line:
            key, value = line.rstrip('\n').split('=')
            info[key.strip()] = value.strip()
    f.close()

    name = info['name']
    version = int(info['activity_version'])
    archive_name = '%s-%s.xo' % (name, version)
    activity_dir = '%s.activity' % name

    f = open('MANIFEST', 'w')
    for path, dirs, files in os.walk('.'):
        if path.startswith('./'): path = path[2:]
        elif path == '.': path = ''
        
        for filename in files:
            if filename == 'MANIFEST':
                continue
            f.write('%s\n' % os.path.join(path, filename))
    f.close()

    # we can't use zipfile because it doesn't preserve permissions *grumble grumble*
    os.chdir('..')
    os.system('zip -r %s %s' % (archive_name, activity_dir))
    os.system('mv %s ./%s' % (archive_name, activity_dir))
    os.chdir(activity_dir)

