import os

from setuptools import setup


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(os.path.dirname(__file__), requirements_file),
              'r') as f:
        requirements = f.read().splitlines()
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


extra_files = package_files('lingua_nostra')

with open("readme.md", "r") as fh:
    long_description = fh.read()

setup(
    name='lingua_nostra',
    version='0.4.5',
    packages=['lingua_nostra', 'lingua_nostra.lang'],
    url='https://github.com/HelloChatterbox/lingua-nostra',
    license='Apache2.0',
    package_data={'': extra_files},
    include_package_data=True,
    install_requires=required('requirements.txt'),
    description="Lingua_Nostra is chatterbox's natural language parser, "
                "it converts natural language into data structures, and data "
                "structures into natural language!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
