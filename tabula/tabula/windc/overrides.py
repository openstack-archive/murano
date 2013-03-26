import horizon

from panel import WinDC

project = horizon.get_dashboard('project')
project.register(WinDC)