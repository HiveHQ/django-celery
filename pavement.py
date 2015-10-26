import os
import sys

from paver.easy import path, sh, needs, task, options, Bunch, cmdopts

PYCOMPILE_CACHES = ['*.pyc', '*$py.class']

options(
    sphinx=Bunch(builddir='.build'),
)


def sphinx_builddir(options):
    return path('docs') / options.sphinx.builddir / 'html'


@task
def clean_docs(options):
    sphinx_builddir(options).rmtree()


@task
@needs('clean_docs', 'paver.doctools.html')
def html(options):
    destdir = path('Documentation')
    destdir.rmtree()
    builtdocs = sphinx_builddir(options)
    builtdocs.move(destdir)


@task
@needs('paver.doctools.html')
def qhtml(options):
    destdir = path('Documentation')
    builtdocs = sphinx_builddir(options)
    sh('rsync -az %s/ %s' % (builtdocs, destdir))


@task
@needs('clean_docs', 'paver.doctools.html')
def ghdocs(options):
    builtdocs = sphinx_builddir(options)
    sh('git checkout gh-pages && \
            cp -r %s/* .    && \
            git commit . -m "Rendered documentation for Github Pages." && \
            git push origin gh-pages && \
            git checkout master' % builtdocs)


@task
@needs('clean_docs', 'paver.doctools.html')
def upload_pypi_docs(options):
    builtdocs = path('docs') / options.builddir / 'html'
    sh('%s setup.py upload_sphinx --upload-dir="%s"' % (
        sys.executable, builtdocs))


@task
@needs('upload_pypi_docs', 'ghdocs')
def upload_docs(options):
    pass


@task
def autodoc(options):
    sh('extra/release/doc4allmods djcelery')


@task
def verifyindex(options):
    sh('extra/release/verify-reference-index.sh')


@task
@cmdopts([
    ('noerror', 'E', 'Ignore errors'),
])
def flake8(options):
    noerror = getattr(options, 'noerror', False)
    complexity = getattr(options, 'complexity', 22)
    migrations_path = os.path.join('djcelery', 'migrations', '0.+?\.py')
    sh("""flake8 djcelery | perl -mstrict -mwarnings -nle'
        my $ignore = (m/too complex \((\d+)\)/ && $1 le %s)
                   || (m{^%s});
        if (! $ignore) { print STDERR; our $FOUND_FLAKE = 1 }
        }{exit $FOUND_FLAKE;
        '""" % (complexity, migrations_path), ignore_error=noerror)


@task
@cmdopts([
    ('noerror', 'E', 'Ignore errors'),
])
def flakeplus(options):
    noerror = getattr(options, 'noerror', False)
    sh('flakeplus --2.6 djcelery', ignore_error=noerror)


@task
@cmdopts([
    ('noerror', 'E', 'Ignore errors')
])
def flakes(options):
    flake8(options)
    flakeplus(options)


@task
def clean_readme(options):
    path('README').unlink_p()
    path('README.rst').unlink_p()


@task
@needs('clean_readme')
def readme(options):
    sh('%s extra/release/sphinx-to-rst.py docs/introduction.rst \
            > README.rst' % (sys.executable, ))
    sh('ln -sf README.rst README')


@task
def bump(options):
    sh('bump -c djcelery')


@task
@cmdopts([
    ('coverage', 'c', 'Enable coverage'),
    ('quick', 'q', 'Quick test'),
    ('verbose', 'V', 'Make more noise'),
])
def test(options):
    sh('%s setup.py test' % (sys.executable, ))


@task
@cmdopts([
    ('noerror', 'E', 'Ignore errors'),
])
def pep8(options):
    noerror = getattr(options, 'noerror', False)
    return sh("""find . -name "*.py" | xargs pep8 | perl -nle'\
            print; $a=1 if $_}{exit($a)'""", ignore_error=noerror)


@task
def removepyc(options):
    sh('find . -type f -a \\( %s \\) | xargs rm' % (
        ' -o '.join('-name "%s"' % (pat, ) for pat in PYCOMPILE_CACHES), ))
    sh('find . -type d -name "__pycache__" | xargs rm -r')


@task
@needs('removepyc')
def gitclean(options):
    sh('git clean -xdn')


@task
@needs('removepyc')
def gitcleanforce(options):
    sh('git clean -xdf')


@task
@needs('flakes', 'autodoc', 'verifyindex', 'test', 'gitclean')
def releaseok(options):
    pass


@task
@needs('releaseok', 'removepyc', 'upload_docs')
def release(options):
    pass


@task
def testloc(options):
    sh('sloccount djcelery/tests')


@task
def loc(options):
    sh('sloccount djcelery')
