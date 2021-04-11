django-newsfeed
===============

.. image:: https://badge.fury.io/py/django-newsfeed.svg
    :target: https://badge.fury.io/py/django-newsfeed

.. image:: https://github.com/saadmk11/django-newsfeed/actions/workflows/test.yaml/badge.svg
    :target: https://github.com/saadmk11/django-newsfeed/actions/workflows/test.yaml

.. image:: https://codecov.io/gh/saadmk11/django-newsfeed/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/saadmk11/django-newsfeed

.. image:: https://github.com/saadmk11/django-newsfeed/workflows/Changelog%20CI/badge.svg
    :target: https://github.com/saadmk11/changelog-ci


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

* **Python**: 3.6, 3.7, 3.8, 3.9
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

Installation
============

Install ``django-newsfeed`` using pip:

.. code-block:: sh

    pip install django-newsfeed


Then add ``newsfeed`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'newsfeed',
    ]

Then add ``newsfeed`` to your projects ``urls.py``:

.. code-block:: python

    urlpatterns = [
        ...
        path('newsfeed/', include('newsfeed.urls', namespace='newsfeed')),
        ...
    ]

Usage
=====
**Available views**

We provide these views out of the box:

* **latest_issue:** ``newsfeed/``
* **issue_list:** ``newsfeed/issues/``
* **issue_detail:** ``newsfeed/issues/<slug:issue_number>/``
* **newsletter_subscribe:** ``newsfeed/subscribe/``
* **newsletter_subscription_confirm:** ``newsfeed/subscribe/confirm/<uuid:token>/``
* **newsletter_unsubscribe:** ``newsfeed/unsubscribe/``

**Templates**

The basic templates are provided for all the views and emails with ``django-newsfeed``.
You can override the templates to add your own design.

Just add ``newsfeed`` directory inside your templates directory
add templates with the same name as the showed tree below.
more on template overriding on the `django docs`_

.. _django docs: https://docs.djangoproject.com/en/3.1/howto/overriding-templates/

Template Tree for ``django-newfeed``:

.. code-block::

    templates
        └── newsfeed
            ├── base.html
            ├── email
            │     ├── email_verification.html
            │     ├── email_verification_subject.txt
            │     ├── email_verification.txt
            │     └── newsletter_email.html
            ├── issue_detail.html
            ├── issue_list.html
            ├── issue_posts.html
            ├── latest_issue.html
            ├── messages.html
            ├── newsletter_subscribe.html
            ├── newsletter_subscription_confirm.html
            ├── newsletter_unsubscribe.html
            └── subscription_form.html

**Subscription confirmation Email**

We send subscription confirmation email to the new subscribers.
you can override these template to change the styles:

.. code-block::

    templates
        └── newsfeed
            ├── email
            │     ├── email_verification.html
            │     ├── email_verification_subject.txt
            │     ├── email_verification.txt


**Admin Actions**

These actions are available from the admin panel:

* **publish issues:**  The selected issues will be published.
* **mark issues as draft:**  The selected issues will be marked as draft.
* **hide posts:**  The selected posts will be hidden from the issues.
* **make posts visible:**  The selected posts will visible on the issues.
* **send newsletters:**  Sends selected newsletters to all the subscribers.
(``send newsletters`` action should be overridden to use a background task queue.
See the `example project`_ to see an example using celery)

**Send Email Newsletter**

We provide a class to handle sending email newsletters to the subscribers.
We do not provide any background task queue by default. But it is fairly easy to set it up.

See the `example project`_ to see an example using ``celery`` and ``celery-beat``.

You can override this template to change the style of the newsletter:

.. code-block::

    templates
        └── newsfeed
            ├── email
            │     └── newsletter_email.html


.. _example project: https://github.com/saadmk11/test-django-newsfeed

Settings Configuration
======================

The below settings are available for ``django-newsfeed``.
Add these settings to your projects ``settings.py`` as required.

``NEWSFEED_SITE_BASE_URL``
--------------------------

* default: ``http://127.0.0.1:8000`` (your sites URL)
* required: True

This settings is required. You need to add your websites URL here in production.
This is used to generate confirmation URL and unsubscribe URL for the emails.

``NEWSFEED_EMAIL_CONFIRMATION_EXPIRE_DAYS``
-------------------------------------------

* default: 3 (after number of days confirmation link expires)
* required: False

This settings tells ``django-newsfeed`` to expire the confirmation link in specified number of days.

``NEWSFEED_EMAIL_BATCH_SIZE``
-----------------------------

* default: 0 (number of emails per batch)
* required: False

This settings is helpful when there are a lot of subscribers.
This settings tells ``django-newsfeed`` to send the specified number of emails per batch.
if its zero (``0``) then all of the emails will be sent together.

``NEWSFEED_EMAIL_BATCH_WAIT``
-----------------------------

* default: 0 (in seconds)
* required: False

This settings tells ``django-newsfeed`` how long it should wait between
each batch of newsletter email sent.

``NEWSFEED_SUBSCRIPTION_REDIRECT_URL``
--------------------------------------

* default: ``/newsfeed/issues/``
* required: False

This is only required if you are not using ``ajax`` request on the subscription form.
The ``JavaScript`` code for ``ajax`` is included with ``django-newsfeed`` and on by default.

``NEWSFEED_UNSUBSCRIPTION_REDIRECT_URL``
----------------------------------------

* default: ``/newsfeed/issues/``
* required: False

This is only required if you are not using ``ajax`` request on the unsubscription form.
The ``JavaScript`` code for ``ajax`` is included with ``django-newsfeed`` and on by default.


Signals
=======

``django-newsfeed`` sends several signals for various actions.
You can add ``receivers`` to listen to the signals and
add your own functionality after each signal is sent.
To learn more about ``signals`` refer to django `Signals Documentation`_.

.. _Signals Documentation: https://docs.djangoproject.com/en/3.1/topics/signals/


Subscriber Signals
------------------


* ``newsfeed.signals.email_verification_sent(instance)``
    Sent after email verification is sent, with ``Subscriber`` instance.

* ``newsfeed.signals.subscribed(instance)``
    Sent after subscription is confirmed, with ``Subscriber`` instance.

* ``newsfeed.signals.unsubscribed(instance)``
    Sent after unsubscription is successful, with ``Subscriber`` instance.


Contribute
==========

See `CONTRIBUTING.rst <https://github.com/saadmk11/django-newsfeed/blob/master/CONTRIBUTING.rst>`_
for information about contributing to ``django-newsfeed``.


License
=======

The code in this project is released under the `GNU General Public License v3.0`_

.. _GNU General Public License v3.0: https://github.com/saadmk11/django-newsfeed/blob/master/LICENSE
