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

retarget
--------

The retarget tool will mass-retarget bugs from one target milestone to
another.
::

    retarget 3.3 z3 z4 1801090


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

- Refactor "update" to a curses GUI.

- Write some "assistence" plugins

  - "default suggestion" plugin or code:

    - If in NEW or ASSIGNED

        - If assignee is *not* a manager: "<assignee> to determine next step for this BZ"
        - If assignee is a manager: "<assignee> to assign to an engineer"

    - If in POST and no Fixed In Version set:

      - "Ken to set Fixed In Version and attach to ET"

    - If in POST and Fixed In Version set: manually verify that fix is in the latest build

    - If in POST/MODIFIED and FIV: "Ken to attach to ET"

- Is there a upstream ticket attached?

- What were the last changes since "last updated time"?

- Shortcuts, like "Ken nextstep" expands to "Ken to determine next step for
  this BZ"

- Highlight "hot_fix_requested" in the report, because these are high-priority.

- Some report of "time spent waiting on development"

- Ignore the following changes:

  - PM Score field update by ccit-bugzilla@redhat.com

  - QA Whiteboard changes

  - TestBlocker keyword addition or removal

  - CC field changes

  - QA Contact changes
