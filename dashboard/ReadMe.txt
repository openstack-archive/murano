# TO DO: 
# 1. Add new functional for services and data centers
# 2. Fix issue with list of services: services table shoudl show services for
#    specific data center

This file is described how to install new tab on horizon dashboard.
We should do the following:
 1. Copy directory 'windc' to directory '/opt/stack/horizon/openstack_dashboard/dashboards/project'
 2. Copy api/windc.py to directory '/opt/stack/horizon/openstack_dashboard/api'
 3. Copy directory 'windcclient' to directory '/opt/stack/horizon/'
 4. Edit file '/opt/stack/horizon/openstack_dashboard/dashboards/project/dashboard.py'
    Add line with windc project:
	
    ...
class BasePanels(horizon.PanelGroup):
    slug = "compute"
    name = _("Manage Compute")
    panels = ('overview',
              'instances',
              'volumes',
              'images_and_snapshots',
              'access_and_security',
              'networks',
              'routers',
              'windc')

    ...

 5. Run the test Django server:
    cd /opt/stack/horizon
    python manage.py runserver 67.207.197.36:8080