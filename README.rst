django-newsfeed
===============

.. image:: https://badge.fury.io/py/django-newsfeed.svg
    :target: https://badge.fury.io/py/django-newsfeed

.. image:: https://travis-ci.com/saadmk11/django-newsfeed.svg?branch=master
    :target: https://travis-ci.com/saadmk11/django-newsfeed

.. image:: https://codecov.io/gh/saadmk11/django-newsfeed/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/saadmk11/django-newsfeed

What is django-newsfeed?
========================

``django-newsfeed`` is a news curator and newsletter subscription package for django.
It can be used to create a news curator website which sends newsletters to their subscribers
also it can be used to add a news subscription section to your website.

Features
========

* Create monthly, weekly or daily issues with ``draft`` issue support.
* Create posts with different categories.
* Archive and display all of the issues in your website.
* Newsletter e-mail subscription (``ajax`` support) with e-mail verification.
* Newsletter e-mail unsubscription (``ajax`` support).
* Sending newsletters for each issue to all the subscribers.
* Fully customizable templates.
* Uses Django's internal tools for sending email.
* Efficient mass mailing support.

Requirements
============

* **Python**: 3.6, 3.7
* **Django**: 2.2, 3.0, 3.1

Example Project
===============

You can view the example project for this package `here`_.
This is a news-curator and newsletter subscription application that only uses this package.
It also uses ``celery``, ``celery-beat`` and ``redis`` to send email newsletters in the background.
The styles in the example project uses ``bootstrap``.

.. _here: https://github.com/saadmk11/test-django-newsfeed


Documentation
=============

Coming Soon!
