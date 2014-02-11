# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
import os
import py_compile
import marshal
import inspect
import re
from command import Command
import pluginlib

class GrepCommand(Command):

    summary = 'Search project for symbol'
    usage = 'SYMBOL'

    max_args = 1
    min_args = 1

    bad_names = ['.svn', 'CVS', '_darcs']

    parser = Command.standard_parser()

    parser.add_option(
        '-x', '--exclude-module',
        metavar="module.name",
        dest="exclude_modules",
        action="append",
        help="Don't search the given module")

    parser.add_option(
        '-t', '--add-type',
        metavar=".ext",
        dest="add_types",
        action="append",
        help="Search the given type of files")

    def command(self):
        self.exclude_modules = self.options.exclude_modules or []
        self.add_types = self.options.add_types or []
        self.symbol = self.args[0]
        self.basedir = os.path.dirname(
            pluginlib.find_egg_info_dir(os.getcwd()))
        if self.verbose:
            print "Searching in %s" % self.basedir
        self.total_files = 0
        self.search_dir(self.basedir)
        if self.verbose > 1:
            print "Searched %i files" % self.total_files

    def search_dir(self, dir):
        names = os.listdir(dir)
        names.sort()
        dirs = []
        for name in names:
            full = os.path.join(dir, name)
            if name in self.bad_names:
                continue
            if os.path.isdir(full):
                # Breadth-first; we'll do this later...
                dirs.append(full)
                continue
            for t in self.add_types:
                if name.lower().endswith(t.lower()):
                    self.search_text(full)
            if not name.endswith('.py'):
                continue
            self.search_file(full)
        for dir in dirs:
            self.search_dir(dir)

    def search_file(self, filename):
        self.total_files += 1
        if not filename.endswith('.py'):
            self.search_text(filename)
            return
        pyc = filename[:-2]+'pyc'
        if not os.path.exists(pyc):
            py_compile.compile(filename)
        if not os.path.exists(pyc):
            # Invalid syntax...
            self.search_text(filename, as_module=True)
            return
        f = open(pyc, 'rb')
        # .pyc Header:
        f.read(8)
        code = marshal.load(f)
        f.close()
        self.search_code(code, filename, [])
        
    def search_code(self, code, filename, path):
        if code.co_name != "?":
            path = path + [code.co_name]
        else:
            path = path
        sym = self.symbol
        if sym in code.co_varnames:
            self.found(code, filename, path)
        elif sym in code.co_names:
            self.found(code, filename, path)
        for const in code.co_consts:
            if const == sym:
                self.found(code, filename, path)
            if inspect.iscode(const):
                if not const.co_filename == filename:
                    continue
                self.search_code(const, filename, path)

    def search_text(self, filename, as_module=False):
        f = open(filename, 'rb')
        lineno = 0
        any = False
        for line in f:
            lineno += 1
            if line.find(self.symbol) != -1:
                if not any:
                    any = True
                    if as_module:
                        print '%s (unloadable)' % self.module_name(filename)
                    else:
                        print self.relative_name(filename)
                print '  %3i  %s' % (lineno, line)
                if not self.verbose:
                    break
        f.close()
                
    def found(self, code, filename, path):
        print self.display(filename, path)
        self.find_occurance(code)

    def find_occurance(self, code):
        f = open(code.co_filename, 'rb')
        lineno = 0
        for index, line in zip(xrange(code.co_firstlineno), f):
            lineno += 1
            pass
        lines = []
        first_indent = None
        for line in f:
            lineno += 1
            if line.find(self.symbol) != -1:
                this_indent = len(re.match(r'^[ \t]*', line).group(0))
                if first_indent is None:
                    first_indent = this_indent
                else:
                    if this_indent < first_indent:
                        break
                print '  %3i  %s' % (lineno, line[first_indent:].rstrip())
                if not self.verbose:
                    break

    def module_name(self, filename):
        assert filename, startswith(self.basedir)
        mod = filename[len(self.basedir):].strip('/').strip(os.path.sep)
        mod = os.path.splitext(mod)[0]
        mod = mod.replace(os.path.sep, '.').replace('/', '.')
        return mod

    def relative_name(self, filename):
        assert filename, startswith(self.basedir)
        name = filename[len(self.basedir):].strip('/').strip(os.path.sep)
        return name

    def display(self, filename, path):
        parts = '.'.join(path)
        if parts:
            parts = ':' + parts
        return self.module_name(filename) + parts
        
