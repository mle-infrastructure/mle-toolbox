try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

import re, os

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(CURRENT_DIR, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def parse_requirements(path):
  with open(os.path.join(CURRENT_DIR, path)) as f:
    return [l.rstrip() for l in f if not (l.isspace() or l.startswith('#'))]


VERSIONFILE="mle_toolbox/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))
git_tar = "https://github.com/RobertTLange/mle-toolbox/archive/v0.2.9.tar.gz"


setup(
     name='mle_toolbox',
     version=verstr,
     author="Robert Tjarko Lange",
     author_email="robertlange0@gmail.com",
     description="Machine Learning Experiment Toolbox",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/RobertTLange/mle-toolbox",
     download_url=git_tar,
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
         "Topic :: Scientific/Engineering :: Artificial Intelligence"
         ],
     packages=find_packages(),
     include_package_data=True,
     zip_safe=False,
     platforms='any',
     python_requires=">=3.6",
     install_requires=parse_requirements(
        os.path.join(CURRENT_DIR, 'requirements', 'requirements.txt')),
     tests_require=parse_requirements(
        os.path.join(CURRENT_DIR, 'requirements', 'requirements-tests.txt')),
     entry_points={
        'console_scripts': [
            'mle=mle_toolbox.toolbox:main',
            'mle-toolbox=mle_toolbox.toolbox:main',
        ]
    }
 )
