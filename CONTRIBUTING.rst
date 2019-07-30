Contributing to the Open Raadsinformatie project
================================================

Want to get involved with the Open Raadsinformatie project? Here's how you can help!

Please take a moment to review this document in order to make the contribution process easy and effective for everyone
involved.

Using the issue tracker
-----------------------

The `issue tracker <https://github.com/openstate/open-raadsinformatie/issues>`_ is the preferred channel for submitting
bug reports, feature requests and pull requests.

Bug reports
-----------

Spot an error in the way data is formatted? Getting an unexpected error when making a call to the API? Then please
submit a bug report. Good bug reports are extremely helpful in order to improve the code, and the project in general.

Some guidelines when submitting a bug report:

- Check if the issue hasn't already been reported.
- Be as detailed as possible: describe the problem thoroughly, so others can try to reproduce it.
- Verify that the problem only occurs within the Open Raadsinformatie project, and not in the original source.

Feature requests
----------------

Feature requests are welcome, but please take a moment to find out whether your idea fits the scope and goals of the
project. It's up to you to make a strong case to convince others of the merits of the feature your are requesting.
Please provide as much detail and context as possible.

Pull requests
-------------

We really like to receive good pull requests for patches, new features or improvements.

Our advice is to first discuss changes, before you start working on a large pull-request (for instance, when
implementing new features or significant refactoring of the code). Otherwise you risk spending time on something that
won't be (directly) merged into the project.

Make sure that your pull request includes proper tests (and that they pass) and documentation.

To submit a pull request, follow this process:

1. `Fork the project <http://help.github.com/fork-a-repo/>`_ and switch to the development branch::

   $ git clone https://github.com/openstate/open-raadsinformatie.git
   $ cd open-raadsinformatie
   $ git checkout development

2. Always make sure you are working with a recent version. To get the latest changes from upstream::

   $ git pull

3. Create a new topic branch to contain your feature, change, or fix::

   $ git checkout -b <topic-branch-name>

4. Push your topic branch up to your fork::

   $ git push origin <topic-branch-name>

5. When you've finished writing your awesome additions to the Open Raadsinformatie project, please rebase your branch
onto the `development` branch before you submit your pull request, in order to prevent us from running into merge
conflicts::

   $ git rebase origin development

6. Open a `pull request <https://help.github.com/articles/using-pull-requests/>`_ with a clear title and description
against the `development` branch.

.. _dev_coding_conventions:

Code formatting
---------------

- We currently target Python 2.7 as a minimum version
- Follow the style you see used in the primary repository - consistency with the rest of the project always trumps other considerations.
- The `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide is used for all Python code.
