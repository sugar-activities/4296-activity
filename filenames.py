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

# Sugar's metadata does not typically provide a file extension, and the
#  filename tends to be unusable. Windows depends on extensions so we need
#  a conversion of metadata -> usable filenames.

from sugar.activity import activity
import os

settings = {}
f = open(os.path.join(activity.get_bundle_path(), 'activity', 'wine.info'), 'U')
for line in f.readlines():
    if '=' in line:
        key, value = line.rstrip('\n').split('=')
        settings[key] = value
f.close()

def guess_extension(metadata):
    #try wine.info settings
    for key in settings:
        if key.startswith('.'):
            if metadata['mime_type'] in settings[key].split(';'):
                return key

    #then try python's standard library
    import mimetypes
    guess = mimetypes.guess_extension(metadata['mime_type'])
    if guess: return guess

    #ok, maybe it's an application/x-extension- type?
    if metadata['mime_type'].startswith(['application/x-extension-']):
        return '.%s' % metadata['mime_type'][len('application/x-extension-'):]
    
    #no? let's call it quits then
    return ''

def guess_filename(metadata):
    def sanitize_filename(string):
        for character in r'\/:*?"<>|':
            string = string.replace(character, '_')
        return string
    
    try:
        # trivial case: someone told us what filename to use
        return sanitize_filename(metadata['suggested_filename'])
    except KeyError:
        ext = guess_extension(metadata)
        if ext:
            # if there is a word that ends with the extension, use it
            # this does the right thing for downloads in English, at least
            for word in metadata['title'].split():
                if word.endswith(ext):
                    return sanitize_filename(word)
            # otherwise, just use the title and extension
            return '%s%s' % (sanitize_filename(metadata['title']), ext)
        else:
            return sanitize_filename(metadata['title'])

def create_dsobject_file(metadata, tmpdir=None):
    import tempfile
    
    if tmpdir is None:
        tmpdir = tempfile.gettempdir()
    
    filename = guess_filename(metadata)
    
    try:
        path = os.path.join(tmpdir, filename)
        fd = os.open(path, os.O_RDWR|os.O_CREAT|os.O_EXCL, 0770)
    except OSError:
        fd, path = tempfile.mkstemp(suffix=filename, dir=tmpdir)
    
    return fd, path

