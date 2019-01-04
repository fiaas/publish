publish - Tool to create a release of a Python package
======================================================

|Build Status| |Codacy Quality Badge| |Codacy Coverage Badge|


.. |Build Status| image:: https://semaphoreci.com/api/v1/fiaas/publish/branches/master/badge.svg
    :target: https://semaphoreci.com/fiaas/publish
.. |Codacy Quality Badge| image:: https://api.codacy.com/project/badge/Grade/bd7d31c7ceac43eb81884b2adc4ba3ed
    :target: https://www.codacy.com/app/fiaas/publish?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=fiaas/publish&amp;utm_campaign=Badge_Grade
.. |Codacy Coverage Badge| image:: https://api.codacy.com/project/badge/Coverage/bd7d31c7ceac43eb81884b2adc4ba3ed
    :target: https://www.codacy.com/app/fiaas/publish?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=fiaas/publish&amp;utm_campaign=Badge_Coverage

publish is a tool to package and release a python project. It will create a changelog and upload artifacts to Github and PyPI.

It is created for and by the `FIAAS project`_, and used for most of our projects.

.. _`FIAAS project`: https://github.com/fiaas


Usage
-----

In order to use publish, you must first install it::

    pip install publish


Under the covers, publish uses github-release_ and twine_ to do most of the work, and those tools require credentials for Github and PyPI to be available in environment variables::

    export GITHUB_TOKEN=gh-token
    export TWINE_USERNAME=pypi-user
    export TWINE_PASSWORD=pypi-pass

In order to know where to upload the artifacts, you must specify an organization, and a repository::

    publish fiaas k8s


Before uploading anything, publish will verify that the current checkout is suitable to be released, and checks the following items:

* Are all files either ignored or in version control?
* Is every change committed?
* Is the currently checked out code tagged with an annotated tag?
* Does that tag use the convention ``v<major>.<minor>.<bugfix>``?

If the answer to all of these is yes, the name of the tag is used as the version to release. A changelog is generated from the git log, source tarballs and wheels are built, the release is created in Github and PyPI, and the files are uploaded.

.. _github-release: https://github.com/j0057/github-release
.. _twine: https://github.com/pypa/twine
