from django.conf import settings
"""
If you want to change the reloading method, define 
INLINETRANS_RELOAD_METHOD in your settings. Default: runserver

Options for this setting::
  * "runserver" 	Django runserver (this does a touch over settings.py)
  * "mod_wsgi"		Apache mod_wsgi, reloads the code with touch wsgi.py
  * "command"		Run RELOAD_COMMAND

"""
RELOAD_METHOD = getattr(settings, 'INLINETRANS_RELOAD_METHOD', 'runserver')
"""
Define a custom INLINETRANS_RELOAD_COMMAND if automatic reload does not work.
The default reload method ("auto") always falls back to RELOAD_COMMAND, 
if it is specified.
"""
RELOAD_COMMAND = getattr(settings, 'INLINETRANS_RELOAD_COMMAND', None)
"""
Increase INLINETRANS_RELOAD_TIME if your program reloads very slowly
"""
RELOAD_TIME = getattr(settings, 'INLINETRANS_RELOAD_TIME', '5')
RELOAD_LOG = getattr(settings, 'INLINETRANS_RELOAD_LOG', 
	'/tmp/autoreload_last.log')
