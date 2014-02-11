import os
from paste.script import pluginlib

egg_dir = os.path.join(os.path.dirname(__file__),
                       'fake_packages', 'FakePlugin.egg')

plugin_file = os.path.join(egg_dir, 'paster_plugins.txt')

def plugin_lines():
    if not os.path.exists(plugin_file):
        return []
    f = open(plugin_file)
    lines = f.readlines()
    f.close()
    return [l.strip() for l in lines if l.strip()]

def test_add_remove():
    prev = plugin_lines()
    pluginlib.add_plugin(egg_dir, 'Test')
    assert 'Test' in plugin_lines()
    pluginlib.remove_plugin(egg_dir, 'Test')
    assert 'Test' not in plugin_lines()
    assert prev == plugin_lines()
    if not prev and os.path.exists(plugin_file):
        os.unlink(plugin_file)
