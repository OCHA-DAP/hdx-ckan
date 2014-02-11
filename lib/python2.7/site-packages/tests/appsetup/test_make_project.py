import urllib
import os
from nose import SkipTest
from paste.fixture import *
import pkg_resources
for spec in ['PasteScript', 'Paste', 'PasteDeploy', 'PasteWebKit',
             'ZPTKit']:
    try:
        pkg_resources.require(spec)
    except pkg_resources.DistributionNotFound, dnf:
        raise SkipTest(repr(dnf))

template_path = os.path.join(
    os.path.dirname(__file__), 'testfiles')

test_environ = os.environ.copy()
test_environ['PASTE_TESTING'] = 'true'

testenv = TestFileEnvironment(
    os.path.join(os.path.dirname(__file__), 'output'),
    template_path=template_path,
    environ=test_environ)

def svn_repos_setup():
    res = testenv.run('svnadmin', 'create', 'REPOS',
                      printresult=False)
    testenv.svn_url = 'file://' + testenv.base_path + '/REPOS'
    assert 'REPOS' in res.files_created
    testenv.ignore_paths.append('REPOS')

def paster_create():
    global projenv
    res = testenv.run('paster', 'create', '--verbose',
                      '--svn-repository=' + testenv.svn_url,
                      '--template=paste_deploy',
                      '--template=webkit',
                      '--template=zpt',
                      '--no-interactive',
                      'ProjectName',
                      'version=0.1',
                      'author=Test Author',
                      'author_email=test@example.com')
    expect_fn = ['tests', 'docs', 'projectname', 'docs',
                 'setup.py', 'ProjectName.egg-info',
                 ]
    for fn in expect_fn:
        fn = os.path.join('ProjectName', fn)
        assert fn in res.files_created
        assert fn in res.stdout
    setup = res.files_created['ProjectName/setup.py']
    setup.mustcontain('test@example.com')
    setup.mustcontain('Test Author')
    setup.mustcontain('0.1')
    setup.mustcontain('projectname.wsgiapp:make_app')
    # ZPTKit should add this:
    setup.mustcontain("include_package_data")
    assert '0.1' in setup
    sitepage = res.files_created['ProjectName/projectname/sitepage.py']
    proj_dir = os.path.join(testenv.cwd, 'ProjectName')
    testenv.run('svn commit -m "new project"',
                cwd=proj_dir)
    testenv.run('python setup.py egg_info',
                cwd=proj_dir,
                expect_stderr=True)
    testenv.run('svn', 'commit', '-m', 'Created project', 'ProjectName')
    # A new environment with a new
    projenv = TestFileEnvironment(
        os.path.join(testenv.base_path, 'ProjectName'),
        start_clear=False,
        template_path=template_path,
        environ=test_environ)
    projenv.environ['PYTHONPATH'] = (
        projenv.environ.get('PYTHONPATH', '') + ':'
        + projenv.base_path)
    projenv.proj_dir = proj_dir

def make_servlet():
    res = projenv.run(
        'paster servlet --verbose --simulate test1',
        cwd=projenv.proj_dir)
    assert not res.files_created and not res.files_updated
    res = projenv.run('paster servlet -vvv test1')
    assert 'projectname/web/test1.py' in res.files_created
    assert 'projectname/templates/test1.pt' in res.files_created
    res = projenv.run('paster servlet -vvv ack.test2')
    assert 'projectname/web/ack/test2.py' in res.files_created
    assert 'projectname/templates/ack/test2.pt' in res.files_created
    res = projenv.run('paster servlet --no-servlet -vvv test3')
    assert 'projectname/web/test3.py' not in res.files_created
    assert 'projectname/templates/test3.pt' in res.files_created
    res = projenv.run('svn status')
    # Make sure all files are added to the repository:
    assert '?' not in res.stdout

def do_pytest():
    res = projenv.run('py.test tests/',
                      cwd=os.path.join(testenv.cwd, 'ProjectName'),
                      expect_stderr=True)
    assert len(res.stderr.splitlines()) <= 1, (
        "Too much info on stderr: %s" % res.stderr)

def config_permissions():
    projenv.writefile('ProjectName.egg-info/iscape.txt',
                      frompath='iscape.txt')
    projenv.writefile('projectname/web/admin/index.py',
                      frompath='admin_index.py')
    projenv.writefile('tests/test_forbidden.py',
                      frompath='test_forbidden.py')
    res = projenv.run('py.test tests/test_forbidden.py',
                      expect_stderr=True)
    assert len(res.stderr.splitlines()) <= 1, (
        "Too much info on stderr: %s" % res.stderr)

def make_tag():
    global tagenv
    res = projenv.run('svn commit -m "updates"')
    res = projenv.run('python setup.py svntag --version=0.5')
    assert 'Tagging 0.5 version' in res.stdout
    assert 'Auto-update of version strings' in res.stdout
    res = testenv.run('svn co %s/ProjectName/tags/0.5 Proj-05'
                      % testenv.svn_url)
    setup = res.files_created['Proj-05/setup.py']
    setup.mustcontain('0.5')
    assert 'Proj-05/setup.cfg' not in res.files_created
    tagenv = TestFileEnvironment(
        os.path.join(testenv.base_path, 'Proj-05'),
        start_clear=False,
        template_path=template_path)

def test_project():
    global projenv
    projenv = None
    yield svn_repos_setup
    yield paster_create
    yield make_servlet
    yield do_pytest
    yield config_permissions
    yield make_tag
    
