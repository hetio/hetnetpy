import os
import pypandoc

long_description = pypandoc.convert('README.md', 'rst', outputfile='README.rst')

os.system("python setup.py register -r pypi")
os.system("python setup.py sdist upload -r pypi")

os.remove('README.rst')
