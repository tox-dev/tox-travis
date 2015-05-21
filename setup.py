from setuptools import setup

setup(
    name='tox-travis',
    description='Seamless integration of Tox into Travis CI',
    long_description=open('README.rst', 'rb').read().decode('utf-8'),
    author='Ryan Hiebert',
    author_email='ryan@ryanhiebert.com',
    url='https://github.com/ryanhiebert/tox-travis',
    license='MIT',
    version='0.1',
    py_modules=['tox_travis'],
    entry_points={
        'tox': ['travis = tox_travis'],
    },
    install_requires=['tox>=2.0'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
