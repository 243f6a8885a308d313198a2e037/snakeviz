#!/usr/bin/env python

import os.path
from pstats import Stats
import json

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

import tornado.ioloop
import tornado.web

from .stats import table_rows, json_stats

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'debug': True,
    'gzip': True
}


class ListDirRow:
    def __init__(self, path, href, file_size, execution_time, total_calls):
        self.path = path
        self.href = href
        self.file_size = file_size
        self.execution_time = execution_time
        self.total_calls = total_calls

    def to_cells(self):
        return [{
            'path': self.path,
            'href': self.href
        }, {
            'file_size': self.file_size
        }, {
            'execution_time': self.execution_time
        }, {
            'total_calls': self.total_calls
        }]


class VizHandler(tornado.web.RequestHandler):
    def get(self, profile_name):
        abspath = os.path.abspath(profile_name)
        if os.path.isdir(abspath):
            self._list_dir(abspath)
        else:
            try:
                s = Stats(profile_name)
            except:
                raise RuntimeError('Could not read %s.' % profile_name)
            self.render(
                'viz.html', profile_name=profile_name,
                table_rows=table_rows(s), callees=json_stats(s))

    def _list_dir(self, path):
        """
        Show a directory listing.

        """
        dir_entries = []
        show_details = True

        row_root = ListDirRow(
            '..', quote(os.path.normpath(os.path.join(path, '..')), safe=''),
            None, None, None)
        dir_entries.append(row_root.to_cells())

        for name in os.listdir(path):
            if name.startswith('.'):
                # skip invisible files/directories
                continue
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname += '/'
            if os.path.islink(fullname):
                displayname += '@'
            size = os.path.getsize(fullname)
            total_calls = None
            execution_time = None
            if show_details and not os.path.isdir(fullname):
                try:
                    s = Stats(fullname)
                    total_calls = s.total_calls
                    execution_time = s.total_tt
                except ValueError:
                    pass
                except:
                    import traceback
                    traceback.print_exc()
                    pass
            row_file = ListDirRow(
                displayname, quote(os.path.join(path, linkname), safe=''),
                size, execution_time, total_calls)
            dir_entries.append(row_file.to_cells())

        self.render(
            'dir.html', dir_name=path, dir_entries=json.dumps(dir_entries))


handlers = [(r'/snakeviz/(.*)', VizHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
