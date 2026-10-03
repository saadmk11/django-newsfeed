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

* **Python**: 3.11, 3.12, 3.13, 3.14
* **Django**: 5.2 (LTS), 6.0, 6.1

Django 5.2 is tested on Python 3.11, 3.12, 3.13, and 3.14.
Django 6.0 and 6.1 are tested on Python 3.12, 3.13, and 3.14.
These are the releases that still receive upstream support.

CI also runs the suite on the Python 3.15 release candidate with Django
5.2, 6.0, and 6.1. A failure there does not fail the supported-version jobs.
There is no Django beta or release candidate to test right now.
Run the Python 3.15 watch locally with:

.. code-block:: sh

    uv python install 3.15
    uv run tox -e py315-django61

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

Or, with uv:

.. code-block:: sh

    uv add django-newsfeed


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

.. _django docs: https://docs.djangoproject.com/en/stable/howto/overriding-templates/

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
* **send newsletters:** Sends the selected newsletters to subscribers in
  the current request. ``respect_schedule`` is ``False``, so a future
  schedule does not block a manual send.

**Send Email Newsletter**

``send_email_newsletter()`` renders each newsletter and sends it to
subscribers. It does not depend on a task runner. Call it from whichever
background runner you already use. Pass primary keys into the task, then
load the newsletters inside the task. A queryset cannot be serialized
into a task payload.

``respect_schedule=False`` matches the admin action and sends the selected
newsletters even when their schedule is still in the future.
``respect_schedule=True`` sends every unsent newsletter whose schedule has
arrived. Omit ``newsletters`` for that scheduled run.

Django tasks
------------

Django 6.0 and later include a task framework. The default backend runs
the task inside ``enqueue()``. Configure ``TASKS`` with a worker backend
when the mail should be sent after the request ends.

.. code-block:: python

    # project/tasks.py
    from django.tasks import task

    from newsfeed.models import Newsletter
    from newsfeed.utils.send_newsletters import send_email_newsletter

    @task
    def send_selected_newsletters(newsletter_ids, respect_schedule=False):
        send_email_newsletter(
            newsletters=Newsletter.objects.filter(pk__in=newsletter_ids),
            respect_schedule=respect_schedule,
        )

    @task
    def send_due_newsletters():
        send_email_newsletter(respect_schedule=True)

Replace the built-in admin action with one that only enqueues the task:

.. code-block:: python

    # project/admin.py
    from django.contrib import admin, messages

    from newsfeed.admin import NewsletterAdmin
    from newsfeed.models import Newsletter
    from project.tasks import send_selected_newsletters

    admin.site.unregister(Newsletter)

    @admin.register(Newsletter)
    class QueuedNewsletterAdmin(NewsletterAdmin):
        actions = ("send_newsletters",)

        @admin.action(description="Send newsletters")
        def send_newsletters(self, request, queryset):
            send_selected_newsletters.enqueue(
                newsletter_ids=list(queryset.values_list("pk", flat=True)),
                respect_schedule=False,
            )
            messages.success(request, "Queued the selected newsletters.")

Celery
------

.. code-block:: python

    # project/tasks.py
    from celery import shared_task

    from newsfeed.models import Newsletter
    from newsfeed.utils.send_newsletters import send_email_newsletter

    @shared_task
    def send_selected_newsletters(newsletter_ids, respect_schedule=False):
        send_email_newsletter(
            newsletters=Newsletter.objects.filter(pk__in=newsletter_ids),
            respect_schedule=respect_schedule,
        )

    @shared_task
    def send_due_newsletters():
        send_email_newsletter(respect_schedule=True)

Point Celery at the Django settings and let it discover ``tasks`` modules:

.. code-block:: python

    # project/celery.py
    from celery import Celery

    app = Celery("project")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()

    app.conf.beat_schedule = {
        "send-due-newsletters": {
            "task": "project.tasks.send_due_newsletters",
            "schedule": 60.0,
        },
    }

The replacement admin action is the same as the Django tasks example,
except the task is started with ``delay``:

.. code-block:: python

    send_selected_newsletters.delay(
        newsletter_ids=list(queryset.values_list("pk", flat=True)),
        respect_schedule=False,
    )

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

Email From address
------------------

Verification messages and newsletters are sent from ``EMAIL_HOST_USER``.

Django 6.1 projects that configure ``MAILERS`` cannot read the ``EMAIL_*``
settings. Set ``DEFAULT_FROM_EMAIL`` in that case. ``django-newsfeed`` uses
``DEFAULT_FROM_EMAIL`` when ``MAILERS`` is configured, and keeps using
``EMAIL_HOST_USER`` otherwise.


Signals
=======

``django-newsfeed`` sends several signals for various actions.
You can add ``receivers`` to listen to the signals and
add your own functionality after each signal is sent.
To learn more about ``signals`` refer to django `Signals Documentation`_.

.. _Signals Documentation: https://docs.djangoproject.com/en/stable/topics/signals/


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
