#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Gal Ben-Zvi",
    author_email='hershkovitz1@mail.tau.ac.il',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="DWIPrep is a robust and easy-to-use pipeline for preprocessing of diverse dMRI data. The transparent workflow dispenses of manual intervention, thereby ensuring the reproducibility of the results. ",
    entry_points={
        'console_scripts': [
            'dwiprep=dwiprep.cli:main',
        ],
    },
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='dwiprep',
    name='dwiprep',
    packages=find_packages(include=['dwiprep', 'dwiprep.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/GalBenZvi/dwiprep',
    version='0.1.0',
    zip_safe=False,
)
