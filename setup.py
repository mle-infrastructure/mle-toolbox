try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

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
            'tabulate',
            'colorclass',
            'terminaltables',
            ]

setup(
     name='mle_toolbox',
     version='0.2.4',
     author="Robert Tjarko Lange",
     author_email="robertlange0@gmail.com",
     description="Machine Learning Experiment Toolbox",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/RobertTLange/mle-toolbox",
     download_url="https://github.com/RobertTLange/mle-toolbox/archive/v0.2.4.tar.gz",
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
            'run-experiment=mle_toolbox.run_experiment:main',
            'retrieve-experiment=mle_toolbox.retrieve_experiment:main',
            'monitor-cluster=mle_toolbox.monitor_cluster:main',
            'report-experiment=mle_toolbox.report_experiment:main'
        ]
    }
 )
