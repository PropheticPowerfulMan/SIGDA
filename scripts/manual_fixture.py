"""Isolated fictitious services used only to capture the demonstration guide."""
import os
from pathlib import Path
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
threading.Thread(target=lambda:(sys.stdin.read(),os._exit(0)),daemon=True).start()
if sys.argv[1]=='public':
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
    from functools import partial
    ThreadingHTTPServer(('127.0.0.1',8858),partial(SimpleHTTPRequestHandler,directory=str(ROOT/'dist/demo'))).serve_forever()
else:
    sys.path.insert(0,str(ROOT/'apps/backend'))
    os.environ['DJANGO_SETTINGS_MODULE']='sigda.settings'
    os.environ['SIGDA_DEMO_PASSWORD']='SIGDA-demo-2026!'
    from django.conf import settings
    settings.DATABASES['default']['NAME']=Path(tempfile.gettempdir())/('sigda-manual-'+os.environ['SIGDA_CAPTURE_ID']+'.sqlite3')
    settings.OPENAI_API_KEY=''
    import django
    django.setup()
    from django.core.management import call_command
    call_command('migrate',verbosity=0)
    call_command('create_workflow_demo_users',verbosity=0)
    call_command('create_maintenance_user','guide-maintenance')
    call_command('runserver','127.0.0.1:8859',use_reloader=False,insecure=True)
