#!/usr/bin/env python
from setuptools import setup


setup(
    name='django-newsfeed',
    version='0.0.1',
    description="""A news curator and newsletter subscription app for django""",
    author='Maksudul Haque',
    author_email='saad.mk112@gmail.com',
    url='https://github.com/saadmk11/django-newsfeed',
    packages=[
        'newsfeed',
    ],
    include_package_data=True,
    install_requires=[
        'Django >= 3.0',
    ],
    license="MIT",
    zip_safe=False,
    keywords='django-newsfeed news curator newsletter subscription',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Framework :: Django :: 3.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
