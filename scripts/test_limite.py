import os
import sys
import django
from django.test import Client

# Ensure project root is on sys.path so 'config' module is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

c = Client()

tests = [
    ('sin(x)/x', 'x', '0', 'both'),
    ('(x**2-1)/(x-1)', 'x', '1', 'both'),
    ('1/x', 'x', 'oo', 'both'),
]

for expr, var, point, direction in tests:
    print('== Test ->', expr, 'x->', point, 'dir=', direction)
    resp = c.post('/calculo/limite/', {'expr': expr, 'var': var, 'point': point, 'direction': direction}, HTTP_HOST='127.0.0.1')
    print('Status:', resp.status_code)
    content = resp.content.decode(errors='replace')
    # Try to locate the Resultado block
    if 'Resultado' in content:
        # crude extraction: find first <pre> after 'Resultado'
        idx = content.find('Resultado')
        pre = content.find('<pre', idx)
        if pre != -1:
            start = content.find('>', pre) + 1
            end = content.find('</pre>', start)
            print('Result snippet:', content[start:end].strip())
        else:
            print('No <pre> result block found; length content:', len(content))
    else:
        print('No Resultado block found; full response preview:')
        print(content[:800])
    print('\n')
