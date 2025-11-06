from algebra.views import biseccion as vb
from types import SimpleNamespace
# Build a fake request-like object with POST dict
class Req(SimpleNamespace):
    def __init__(self, post):
        super().__init__()
        self.POST = post
        self.method='POST'

cases = [ ('1/2','2'), ('½','2'), ('0.5','2'), ('1','2') ]
for a,b in cases:
    req = Req({'function':'log(x)-e**(-x)=0','a':a,'b':b,'tol':'1e-6','maxit':'100'})
    try:
        resp = vb(req)
        print('CASE',a,'-> view returned', type(resp))
    except Exception as e:
        print('CASE',a,'-> ERROR',repr(e))

# Also test parse_number indirectly by importing and evaluating via exec
from inspect import getsource
src = getsource(vb)
# Extract parse_number definition
if 'def parse_number' in src:
    start = src.index('def parse_number')
    sub = src[start: start+1000]
    print('\nparse_number snippet:\n', sub.splitlines()[:20])
else:
    print('parse_number not found')
