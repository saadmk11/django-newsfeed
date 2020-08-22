#!/usr/bin/env python
from setuptools import setup

readme = open('README.rst').read()

setup(
    name='django-newsfeed',
    version='0.0.5',
    description="""A news curator and newsletter subscription app for django""",
    long_description=readme,
    author='Maksudul Haque',
    author_email='saad.mk112@gmail.com',
    url='https://github.com/saadmk11/django-newsfeed',
    packages=[
        'newsfeed',
    ],
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'Django >= 2.2',
    ],
    license="MIT",
    zip_safe=False,
    keywords='django-newsfeed news curator newsletter subscription',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django :: 3.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
