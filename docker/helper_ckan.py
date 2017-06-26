"""tools to setup and configure a docker-compose stack."""

import fcntl
import getpass
import re
import os
# import requests
import socket
import struct
# import sys


class DockerHelper(object):
    """encapsulates some dirty logic for configuring a docker stack."""

    version = '0.2'

    def __init__(self):
        """fake initializer."""
        pass

    @classmethod
    def fromcontainer(cls, templates_root_path='tmp', var_pattern=['${', '}'],
                      private_vars_separator=':::'):
        """initializer for in-container service startup."""
        obj = cls()
        obj.env = os.environ
        obj.private_vars_separator = private_vars_separator
        obj.templates_root_path = templates_root_path
        obj.var_pattern = var_pattern
        return obj

    @classmethod
    def fromhost(cls, templates_root_path='tmp', var_pattern=['${', '}'],
                 private_vars_separator=':::'):
        """initializer for docker-compose setups."""
        obj = cls()
        obj.custom_vars = dict()
        obj.env = dict()
        obj.env['DOCKER0_ADDR'] = obj._get_ip_address('docker0')
        obj.private_files = dict()
        obj.private_repo = dict.fromkeys(['base_url', 'files',
                                          'user', 'pass'])
        obj.private_vars_separator = private_vars_separator
        obj.templates_root_path = templates_root_path
        obj.var_pattern = var_pattern
        return obj

    def build_file(self, string):
        """convert env var string to a file."""
        string = string.replace('"', '').split(self.private_vars_separator)
        return '\n'.join(string)

    def _build_string(self, file_name):
        """import a file (e.g. rsa key or certificate) into a string."""
        with file(file_name) as f:
            return f.read().replace('\n', self.private_vars_separator)

    @staticmethod
    def _get_ip_address(ifname):
        """get the assigned ip address of an interface."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    # def _file_path(self, file_name):
    #     return '/'.join([self.files_folder, file_name])

    @staticmethod
    def _create_file(file_name, content, private=True,
                     overwrite=False, uid=0, gid=0):
        """create a special file from the content provided."""
        if private:
            chmode = 0o400
        else:
            chmode = 0o644

        if os.path.isfile(file_name) and not overwrite:
            print 'File', file_name, 'aleady exists. Skipping.'
            return

        with open(file_name, 'w') as f:
            f.write(content)

        os.chown(file_name, uid, gid)
        os.chmod(file_name, chmode)

    def create_special_file(self, file_name, content_var, private=True,
                            overwrite=False, uid=0, gid=0):
        """create file_name containing the value of self.env[content_var]."""
        if content_var not in self.env:
            print 'Cannot find variable named', content_var
            print 'Skipping creation of file', file_name
            return
        content = self.build_file(self.env[content_var])
        self._create_file(file_name, content, private=private,
                          overwrite=overwrite, uid=uid, gid=gid)

    def _replace_pattern(self, text):
        """replace var_pattern-ed env keys with their corresponding value."""
        sub_vars = re.findall(r'\$\{([0-9a-zA-Z_]+)\}', text.rstrip())
        for var in sub_vars:
            if var not in self.env:
                print var, 'not found in env!!!'
                # print 'Quitting'
                # sys.exit(1)
                continue
            if self.env[var] is None:
                continue
            var_pattern = list(self.var_pattern)
            var_pattern.insert(1, var)
            text = text.replace(''.join(var_pattern), self.env[var])
        # make sure the dollar signs required in service config are there
        text = text.replace('%', '$')
        return text

    def import_vars(self, vars_file='vars'):
        """load vars from vars file, substitution included, into self.env."""
        with file(vars_file) as f:
            for l in f.readlines():
                l = l.rstrip()
                # skip comment or short lines
                if (len(l) < 2) or ('=' not in l) or (l.startswith('#')):
                    continue
                label, value = l.split('=')
                self.env[label] = self._replace_pattern(value)
                # if value matches this pattern: $((something+somethingelse))
                regexp_match = re.match(r'\$\(\(.+\+([0-9]+)\)\)', value)
                if regexp_match:
                    try:
                        port_inc = regexp_match.group(1)
                    except IndexError:
                        print 'Error trying to set the port number for:', label
                    else:
                        # i don't like hardconding baseport key name
                        value = int(self.env['HDX_BASEPORT']) + int(port_inc)
                        self.env[label] = str(value)
                # custom vars (a variable deduced from another)
                if label in self.custom_vars:
                    name, regex, subst = self.custom_vars[label]
                    self.env[name] = re.sub(regex, subst, value)

    def _find_templates(self):
        """find all teplates files in the specified path."""
        templates = []

        for root, dirs, files in os.walk(self.templates_root_path):
            for file_name in files:
                if file_name.endswith('.tpl'):
                    templates.append(os.path.join(root, file_name))

        return templates

    def create_config_files(self):
        """create config files from templates and env vars."""
        for template_file in self._find_templates():
            file_name = re.sub(r'\.tpl$', '', template_file)
            # skip if dst exists
            if os.path.isfile(file_name):
                print file_name, 'already created. Remove it to refresh.'
                print 'Skipping.'
                continue
            with open(template_file) as t:
                content = t.read()
            self._create_file(file_name, self._replace_pattern(content))

    def _configure_remote_repo(self):
        """configure params to be able to connect to a remote repo."""
        if not self.private_repo['base_url']:
            self.private_repo['base_url'] = raw_input("Your repo's base url: ")
        if not self.private_repo['user']:
            self.private_repo['user'] = raw_input('Your repo username: ')
        if not self.private_repo['pass']:
            self.private_repo['pass'] = getpass.getpass('Your repo password: ')

    def fetch_remote_private_file(self, file_name, files_folder='.files'):
        """
        fetch a file from a remote repo and save it locally.

        uses url and credentials from self.private_repo
        save the file under files_folder directory.
        """
        file_path = '/'.join([files_folder, file_name])
        if os.path.isfile(file_path):
            return True
        if not os.path.isdir(files_folder):
            os.makedirs(files_folder)
        self._configure_remote_repo()
        url = ''.join([self.private_repo['base_url'], file_name])
        user = self.private_repo['user']
        password = self.private_repo['pass']
        try:
            req = requests.get(url, auth=(user, password))
        except requests.exceptions.ConnectionError:
            print 'There was a problem connecting to your repo host.'
            print 'Fetch of', file_name, 'skipped.'
        else:
            if req.status_code == 200:
                with open(file_path, 'w') as f:
                    f.write(req.text)
                return True
            elif req.status_code == 404:
                print 'There was a problem with the url path or file name.'
                print 'Fetch of', file_name, 'skipped.'
            elif req.status_code == 401 or req.status_code == 403:
                print 'There was a problem with your repo credentials.'
                print 'Fetch of', file_name, 'skipped.'
            else:
                print 'There was a problem connecting to your repo.'
                print 'Fetch of', file_name, 'skipped.'
        return False

    def import_remote_private_files(self, files_folder='.files'):
        """import private files from a remote repo."""
        for var_name, file_name in self.private_repo['files']:
            if self.fetch_remote_private_file(file_name):
                file_path = '/'.join([files_folder, file_name])
                self.env[var_name] = self._build_string(file_path)


def main():
    """show a use-case."""
    #
    s = DockerHelper.fromcontainer(templates_root_path='/srv')
    ssh_folder = '/root/.ssh'
    ssh_key = '/'.join([ssh_folder, 'id_rsa'])
    ssh_pub = '.'.join([ssh_key, 'pub'])
    if not os.path.isdir(ssh_folder):
        os.makedirs(ssh_folder)

    s.create_special_file(ssh_pub, 'HDX_SSH_PUB', private=False)
    s.create_special_file(ssh_key, 'HDX_SSH_KEY', private=True)

    s.create_config_files()

if __name__ == '__main__':
    main()
