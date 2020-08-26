Contributing
------------

Contribution is always welcome and appreciated. Feel Free to submit
issues or pull requests by following the guide below.

Report A Bug
------------

Report bugs at https://github.com/saadmk11/django-newsfeed/issues.

Please include these on your bug report:

* How you came across this bug.
* Details about your local setup.
* Version of python and django you are using.
* Traceback of the error (if any).

Write Documentation
-------------------

If you find anything that may require more explaining or is not documented
feel free to update it and submit a pull request.

Request A New Feature
---------------------

You can add your feature request `here`_.

Please include these on your feature request:

* Detailed information of your feature request.
* Explain how it will work.

.. _here: https://github.com/saadmk11/django-newsfeed

Fix Bugs
--------

Look through the `GitHub issues`_ for bugs. If you find anything you want to work
on feel free to get started on it.

Implement A Feature
-------------------

If you find any issue on the projects `GitHub issues`_ with ``Feature`` tag
and you want to implement it you are more than welcome to leave a comment on
the issue we will get back to you soon.

Give Feedback
-------------

If you are using this package we would love to know your experience and suggestions.
You can open a `GitHub issues`_ and we can talk more about it.
Feedbacks are always appreciated.

.. _GitHub issues: https://github.com/saadmk11/django-newsfeed


Setting up the project for development
--------------------------------------

Follow the steps below to set up ``django-newsfeed`` locally.

1. Fork ``django-newsfeed`` repository on GitHub.

   ``https://github.com/saadmk11/django-newsfeed``

2. Clone the forked repository on your local machine:

.. code-block:: sh

    $ git clone git@github.com:<your-github-username>/django-newsfeed.git

3. change directory to ``django-newsfeed`` and install ``django-newsfeed`` inside a virtualenv:

.. code-block:: sh

    $ mkvirtualenv django-newsfeed     # you can use virtualenv instead of virtualenvwrapper
    $ cd django-newsfeed/
    $ python setup.py develop

4 Setup and Run the development server:

.. code-block:: sh

    $ python manage.py migrate
    $ python manage.py runserver       # http://127.0.0.1:8000/

5. Create a new branch for local development:

.. code-block:: sh

    $ git checkout -b <your-new-branch-name>


6. Make the changes you need. Include tests if you have made any changes to the code.

7. Run tests to make sure everything is working properly:

.. code-block:: sh

    $ tox

run ``pip install tox`` if its not already installed in your machine

8. Commit the changes and push it to GitHub:

.. code-block:: sh

    $ git add .
    $ git commit -m "<Commit message about the changes you made>"
    $ git push <your-new-branch-name>

9. Create a pull request to ``django-newsfeed``
