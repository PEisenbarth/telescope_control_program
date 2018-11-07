from .OverallSettings import OverallSettings

print '''
\t\t\t------------------------------------
\t\t\t  Wetton Telescope control program
\t\t\t------------------------------------
\n
'''
print 'Starting telescope telescopecontrol program'
OVST = OverallSettings()
from .commands import *
print 'Control program ready to use'
print 'Note: to close the program, please use quit() or exit()'
# Start ipython with above configurations


__version__ = '0.1'