import sys
import os
import shutil
import pkg_resources

here = os.path.dirname(__file__)
base = os.path.dirname(here)
fake_packages = os.path.join(here, 'fake_packages')
sys.path.append(fake_packages)
sys.path.append(here)
sys.path.insert(0, base)

here = os.path.dirname(__file__)
egg_info_dir = os.path.join(here, 'fake_packages', 'FakePlugin.egg',
                            'EGG-INFO')
info_dir = os.path.join(here, 'fake_packages', 'FakePlugin.egg',
                        'FakePlugin.egg-info')

if not os.path.exists(egg_info_dir):
    try:
        os.symlink(info_dir, egg_info_dir)
    except:
        shutil.copytree(info_dir, egg_info_dir)

pkg_resources.working_set.add_entry(fake_packages)
pkg_resources.working_set.add_entry(base)

if not os.environ.get('PASTE_TESTING'):
    output_dir = os.path.join(here, 'appsetup', 'output')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
pkg_resources.require('FakePlugin')

