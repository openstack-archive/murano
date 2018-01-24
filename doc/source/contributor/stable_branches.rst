.. _stable_branches:

==============================
Backporting to stable/branches
==============================

Since murano is a big-tent OS project it largely follows the
`OpenStack stable branch guide <https://docs.openstack.org/project-team-guide/stable-branches.html>`_

Upstream support phases
~~~~~~~~~~~~~~~~~~~~~~~

#. Phase I (first 6 months): All bugfixes (which meet the stable port criteria,
   described in OS stable branch policy) are appropriate
#. Phase II (6-12 months): Only critical bugfixes and
   security patches are acceptable
#. Phase III (more than 12 months): Only security
   patches are acceptable

In order to accept a change into $release it must first be accepted into all
releases back to master.

There are two notable exceptions to the support phases rule:

- murano-apps repository:
  We recognise, that murano apps have different lifecycle than main murano
  repository. Most of the time new apps are being written for already released
  versions of murano, not for master. Having a rich collection of apps is one of
  the goals of murano-apps repository, therefore we accept backports of apps and
  app features to previous release branches. This is done on a case by case basis
  and should be discussed with PTL and Murano core members on IRC or Mailing
  List. However we believe, that submitting an app to stable branch only means
  that author of the patch is not going to support the app. Therefore for the app
  to get backported it still has to be first accepted to master and all
  subsequent releases.

- murano core library patches: Murano Core Library is an
  app, that provides core functionality and classes for other murano apps. It
  shares a lot of properties of regular murano apps and the rationale behind
  allowing backports of MuranoPL code from master to stable branches is basically
  the same: low regression risks during upgrades, high adoption impact. However
  since core library is much more sensitive app, backports to it should be taken
  more seriously and should be discussed on IRC and Mailing List and receive
  PTL's approval.

These two exceptions do not mean, that we're free to backport
any code from master to stable branches. Instead they show, that murano team
recognises the importance of these two areas of murano project and treats
exceptions to those slightly more liberally than to other parts of murano
project.

Bug nomination process
~~~~~~~~~~~~~~~~~~~~~~

Whenever you file a bug, or see a bug, that you think
is eligible for backporting in stable branch nominate it for the corresponding
series. If bug reporter does not nominate the bug for eligible branch — this is
done by murano bug supervisor during triaging/confirmation process. In case it
is not clear whether the bug is eligible or not or if you do not have
permissions to nominate a bug for series you can set
`$release-backport-potential` tag (for example `liberty-backport-potential`).
Murano team is holding bi-weekly meetings on IRC (as part of regular community
meetings) to triage and nominate bugs for stable backports.
