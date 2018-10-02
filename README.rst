rhcephbugs
==========

Common code for managing RH Ceph Storage bugs.

Some of these utilities can run in Jenkins, others are human decision
amplifiers.

triage
------

The triage tool has two commands, ``update`` and ``report``.

The ``update`` subcommand will query all BZs for a release and prompt the user
to describe the next action for each BZ.

The ``report`` subcommand will print a report to STDOUT for this release.


comment-on-git example
----------------------

Jenkins' Git plugin will set some environment variables like ``GIT_URL``,
``GIT_BRANCH``,  ``GIT_PREVIOUS_SUCCESSFUL_COMMIT``, and ``GIT_COMMIT``. The
``comment-on-git`` command will parse these environment variables to look at a
range of git commits and add comments in Bugzilla bugs::

    $ PKG=ceph \
      GIT_URL=git://pkgs.devel.redhat.com/rpms/ceph \
      GIT_BRANCH='ceph-2-rhel-7' \
      GIT_PREVIOUS_SUCCESSFUL_COMMIT=442839cc5cb3e4024ed172213d27d5e8951901f7 \
      GIT_COMMIT=3e53e1c54a7a5da024ae8a053e05e8648644086c \
      comment-on-git


Features
--------

- Comment in BZ when RHEL and Ubuntu dist-git changes.

TODO List
---------

- Comment in BZ with the exact commits that were pushed to ``-patches`` branch.
  (Only do this if it was a simple push without any rebase).

- Listen and parse dist-git messagebus messages.

- Listen and parse Gerrit plugin events (``-patches`` branches).

- Update "Fixed In Version" field when dist-git changes.

- Move bug to "MODIFIED" when both RHEL and Ubuntu "Fixed In Version" are set.

- Attach bug to Errata Tool advisory when build completes.

TODO List for "triage"
----------------------

- Write some "assistence" plugins

- Is there a upstream ticket attached?

- What were the last changes since "last updated time"?

- What is the BZ assignee's name?

- Show updated time in relative time ("last modified 3 minutes ago")

- Shortcuts, like "Ken nextstep" expands to "Ken to determine next step for
  this BZ"

- If we have many bugs, show a progress indicator, like "1/63"
