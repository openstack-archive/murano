# TO DO: 
# 1. Fix issue with Create button  
# 2. Create simple form for Windows Data Center deploy
# 3. Remove extra code
#

This file is described how to install new tab on horizon dashboard.
We should do the following:
 1. Copy directory 'windc' to directory '/opt/stack/horizon/openstack_dashboard/dashboards/project'
 2. Edit file '/opt/stack/horizon/openstack_dashboard/dashboards/project/dashboard.py'
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

 3. Run the test Django server:
    cd /opt/stack/horizon
    python manage.py runserver 67.207.197.36:8080