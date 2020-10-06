try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

from os import path
this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

requires = [
            'numpy==1.17.4',
            'pandas==0.25.3',
            'scipy==1.3.2',
            'h5py==2.10.0',
            'tensorboard',
            'tensorboardX',
            'matplotlib==3.1.2',
            'seaborn==0.9.0',
            'commentjson',
            'pyyaml',
            'scikit-optimize',
            'torch',
            'torchvision',
            'colorclass',
            'terminaltables',
            'gitpython',
            'scp',
            'sshtunnel',
            'pickledb',
            'google-cloud-storage',
                        'tabulate']

setup(
     name='mle_toolbox',
     version='0.2.1',
     author="Robert Tjarko Lange",
     author_email="robertlange0@gmail.com",
     description="Machine Learning Experiment Toolbox",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/RobertTLange/mle-toolbox",
     download_url="https://github.com/RobertTLange/mle-toolbox/archive/v_01.tar.gz",
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent"],
     packages=find_packages(),
     include_package_data=True,
     zip_safe=False,
     platforms='any',
     install_requires=requires,
     entry_points={
        'console_scripts': [
            'run-experiment=mle_toolbox.run_experiment:main',
            'retrieve-experiment=mle_toolbox.retrieve_experiment:main',
            'monitor-cluster=mle_toolbox.monitor_cluster:main'
        ]
    }
 )


