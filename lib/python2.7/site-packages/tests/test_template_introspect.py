import os
from paste.script import templates

tmpl_dir = os.path.join(os.path.dirname(__file__), 'sample_templates')

def test_find():
    vars = templates.find_args_in_dir(tmpl_dir, True)
    assert 'a' in vars
    assert vars['a'].default is templates.NoDefault
    assert 'b' in vars
    assert vars['b'].default == 1
    assert len(vars) == 2
    
