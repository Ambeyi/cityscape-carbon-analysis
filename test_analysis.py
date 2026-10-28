import tempfile
import unittest
import pandas as pd
from analyze import summarize, run, MODE, VALUE

class Tests(unittest.TestCase):
    def test_summary(self):
        _,s=summarize(pd.DataFrame({MODE:['A']*3,VALUE:[1,2,3]}))
        self.assertEqual(s.n.iloc[0],3)
        self.assertEqual(s['mean'].iloc[0],2)
        self.assertEqual(s.sd.iloc[0],1)
        self.assertAlmostEqual(s.ci95_upper.iloc[0],4.4841377117)
    def test_missing_and_singleton(self):
        d,s=summarize(pd.DataFrame({MODE:['A','A',None],VALUE:[2,None,8]}))
        self.assertEqual(len(d),1)
        self.assertTrue(pd.isna(s.ci95_upper.iloc[0]))
    def test_invalid(self):
        for v in [-1,float('inf'),'bad']:
            with self.assertRaises(ValueError): summarize(pd.DataFrame({MODE:['A'],VALUE:[v]}))
    def test_tests_and_exports(self):
        with tempfile.TemporaryDirectory() as p:
            r=run(pd.DataFrame({MODE:['A']*3+['B']*3,VALUE:[1,2,3,4,5,6]}),p)
            self.assertAlmostEqual(r['anova']['F'],13.5)
            self.assertEqual(r['complete_rows'],6)
            self.assertEqual(len(pd.read_csv(p+'/transport_summary.csv')),2)

if __name__=='__main__': unittest.main()
