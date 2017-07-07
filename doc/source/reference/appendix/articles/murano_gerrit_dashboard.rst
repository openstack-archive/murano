Murano Gerrit Dashboard
=======================

Description
-----------
If you would like to contribute to murano by reviewing patches to
murano-related projects — you can use this gerrit dashboard, or create your own
using
`Gerrit Dash Creator <http://gerrit-dash-creator.readthedocs.io/en/latest/>`__

URL
---

::

   https://review.openstack.org/#/dashboard/?foreach=%28project%3A%5E.%2A%2F.%2Amurano.%2A+OR+project%3Aopenstack%2Fyaql%29+NOT+label%3AWorkflow%3C%3D%2D1+NOT+label%3ACode%2DReview%3C%3D%2D2+status%3Aopen&title=Murano&My+Patches=owner%3Aself&You+are+a+reviewer%2C+but+haven%27t+voted+in+the+current+revision=NOT+label%3ACode%2DReview%3C%3D2%2Cself+reviewer%3Aself+NOT+owner%3Aself&Need+Feedback=NOT+label%3ACode%2DReview%3C%3D2+NOT+label%3AVerified%3C%3D%2D1+NOT+owner%3Aself&Passed+Jenkins%2C+No+Negative+Feedback=label%3ACode%2DReview%3E%3D1+NOT+label%3ACode%2DReview%3C%3D%2D1+AND+NOT+label%3AVerified%3C%3D%2D1+NOT+owner%3Aself+NOT+reviewer%3Aself+limit%3A50&Maybe+Review%3F=NOT+owner%3Aself+NOT+reviewer%3Aself+limit%3A25&My+%2B1s=label%3ACode%2DReview%3D1%2Cself+limit%3A25&Need+final+%2B2=label%3ACode%2DReview%3E%3D2+NOT+label%3ACode%2DReview%3C%3D%2D1+NOT+label%3AVerified%3C%3D%2D1+NOT+label%3ACode%2DReview%3C%3D2%2Cself+NOT+owner%3Aself+limit%3A25&My+%2B2s=label%3ACode%2DReview%3D2%2Cself+limit%3A25

`View this dashboard <https://review.openstack.org/#/dashboard/?foreach=%28project%3A%5E.%2A%2F.%2Amurano.%2A+OR+project%3Aopenstack%2Fyaql%29+NOT+label%3AWorkflow%3C%3D%2D1+NOT+label%3ACode%2DReview%3C%3D%2D2+status%3Aopen&title=Murano&My+Patches=owner%3Aself&You+are+a+reviewer%2C+but+haven%27t+voted+in+the+current+revision=NOT+label%3ACode%2DReview%3C%3D2%2Cself+reviewer%3Aself+NOT+owner%3Aself&Need+Feedback=NOT+label%3ACode%2DReview%3C%3D2+NOT+label%3AVerified%3C%3D%2D1+NOT+owner%3Aself&Passed+Jenkins%2C+No+Negative+Feedback=label%3ACode%2DReview%3E%3D1+NOT+label%3ACode%2DReview%3C%3D%2D1+AND+NOT+label%3AVerified%3C%3D%2D1+NOT+owner%3Aself+NOT+reviewer%3Aself+limit%3A50&Maybe+Review%3F=NOT+owner%3Aself+NOT+reviewer%3Aself+limit%3A25&My+%2B1s=label%3ACode%2DReview%3D1%2Cself+limit%3A25&Need+final+%2B2=label%3ACode%2DReview%3E%3D2+NOT+label%3ACode%2DReview%3C%3D%2D1+NOT+label%3AVerified%3C%3D%2D1+NOT+label%3ACode%2DReview%3C%3D2%2Cself+NOT+owner%3Aself+limit%3A25&My+%2B2s=label%3ACode%2DReview%3D2%2Cself+limit%3A25>`__


Configuration
-------------

::


    [dashboard]
    title = Murano
    description = Murano Review Inbox
    foreach = (project:^.*/.*murano.* OR project:openstack/yaql) NOT label:Workflow<=-1 NOT label:Code-Review<=-2 status:open

    [section "My Patches"]
    query = owner:self

    [section "You are a reviewer, but haven't voted in the current revision"]
    query = NOT label:Code-Review<=2,self reviewer:self NOT owner:self

    [section "Need Feedback"]
    query = NOT label:Code-Review<=2 NOT label:Verified<=-1 NOT owner:self

    [section "Passed Jenkins, No Negative Feedback"]
    query = label:Code-Review>=1 NOT label:Code-Review<=-1 AND NOT label:Verified<=-1 NOT owner:self NOT reviewer:self limit:50

    [section "Maybe Review?"]
    query = NOT owner:self NOT reviewer:self limit:25

    [section "My +1s"]
    query = label:Code-Review=1,self limit:25

    [section "Need final +2"]
    query = label:Code-Review>=2 NOT label:Code-Review<=-1 NOT label:Verified<=-1 NOT label:Code-Review<=2,self NOT owner:self limit:25

    [section "My +2s"]
    query = label:Code-Review=2,self limit:25



