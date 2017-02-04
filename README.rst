rhcephbugs
==========

Common code for managing RH Ceph Storage bugs. We use this with Jenkins jobs to
automate certain bug actions.

Example
-------

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
