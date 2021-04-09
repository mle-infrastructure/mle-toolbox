try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

import re
from os import path
this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

requires = [
            'numpy',
            'pandas',
            'dotmap',
            'h5py',
            'toml',
            'pyyaml',
            'commentjson',
            'pickledb',
            'gitpython',
            'scp',
            'paramiko',
            'sshtunnel',
            'rich',
            'termplotlib',
            ]


VERSIONFILE="mle_toolbox/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))
git_tar = "https://github.com/RobertTLange/mle-toolbox/archive/v0.2.6.tar.gz"


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
         "Programming Language :: Python :: 3.6",
         "Programming Language :: Python :: 3.7",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent"],
     packages=find_packages(),
     include_package_data=True,
     zip_safe=False,
     platforms='any',
     python_requires=">=3.6",
     install_requires=requires,
     entry_points={
        'console_scripts': [
            'mle=mle_toolbox.toolbox:main',
            'mle-toolbox=mle_toolbox.toolbox:main',
        ]
    }
 )
