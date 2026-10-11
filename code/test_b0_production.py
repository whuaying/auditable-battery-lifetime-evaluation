"""B0 regression tests execute the actual production assignment nodes."""
import ast, unittest
from pathlib import Path
import numpy as np
from decision_contract import opportunities, timing_loss
tree=ast.parse((Path(__file__).parent/'04_run_replacement.py').read_text())
nodes=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('b0_grid','b0') for t in n.targets)]
code=compile(ast.Module(body=nodes,type_ignores=[]),'production_b0','exec')
def actual(l,h,delta):
    scope=dict(l=l,h=h,delta=delta,np=np,opportunities=opportunities)
    exec(code,scope)
    return scope['b0']
class B0(unittest.TestCase):
    def test_all_grids(self):
        for l in (50,100):
            for h in (500,1000,1500):
                for d in (25,50,100):
                    a=actual(l,h,d)
                    feasible=opportunities(l,h,d)
                    self.assertIn(a,feasible)
                    self.assertEqual(a,sorted(feasible,key=lambda v:(abs(v-1000),v))[0])
    def test_earlier_tie(self):
        self.assertEqual(actual(50,1500,100),950.)
    def test_absolute_residual_window(self):
        self.assertEqual(actual(100,500,50),500.)
        np.testing.assert_array_equal(timing_loss(np.array([500.]),np.array([800.]),100,500,4),[0.])
if __name__=='__main__':unittest.main()
