import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from process_data import aggregate, rating
from fetch_kobo import fetch

class PipelineTests(unittest.TestCase):
    def rows(self,n=5):
        return [dict(viaje='2026-09-24',hr=5,education=4,logistics=3,im=2,sm=1,acompa=4,estadia=4,comidas=4,vuelos=4,nombre='PRIVATE',feedback='Useful comment',_id=i) for i in range(n)]
    def test_privacy_and_small_groups(self):
        self.assertEqual(aggregate(self.rows(1))['buckets'],[])
        data=aggregate(self.rows());self.assertNotIn('PRIVATE',str(data));self.assertNotIn('_id',str(data))
        self.assertEqual(data['buckets'][0]['composites']['support'],{'sum':15.0,'n':5})
    def test_missing_not_zero_and_question_suppression(self):
        rows=self.rows();rows[0]['hr']=None
        data=aggregate(rows, min_responses=5)['buckets'][0]
        self.assertIsNone(data['metrics']['hr']['counts']);self.assertIsNone(data['composites']['support']['n'])
        self.assertEqual(data['composites']['trip']['n'],5)
        for v in [True,0,6,2.5,'nan','bad',None]:self.assertIsNone(rating(v))
    def test_dedup_and_group_paths(self):
        rows=self.rows();rows.append(rows[0]);rows[0]['group/hr']=rows[0].pop('hr')
        self.assertEqual(aggregate(rows)['buckets'][0]['responses'],5)
    def test_no_token_leak_to_pagination(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self):return b'{"results": [], "next": "https://evil.example/data"}'
        with patch('fetch_kobo.build_opener') as factory:
            factory.return_value.open.return_value=Response()
            with self.assertRaisesRegex(ValueError,'cross-origin'):fetch('https://kf.kobotoolbox.org','abc','secret')
            self.assertEqual(factory.return_value.open.call_count,1)
    def test_two_response_trip_and_comments(self):
        rows=self.rows(2);rows[0]['durante/apoyo']=' Bring materials ';rows[0]['header_3']='  '
        bucket=aggregate(rows)['buckets'][0]
        self.assertEqual(bucket['responses'],2)
        self.assertEqual(bucket['metrics']['hr']['counts'],[0,0,0,0,2])
        self.assertIn({'category':'apoyo','text':'Bring materials'},bucket['comments'])
        self.assertNotIn('nombre',str(bucket));self.assertNotIn('PRIVATE',str(bucket))
        self.assertEqual(aggregate(self.rows(1))['buckets'],[])

    def test_invalid_dates(self):
        rows=self.rows();rows[0]['viaje']='invalid'
        self.assertEqual(aggregate(rows)['invalid_date_responses'],1)

if __name__=='__main__':unittest.main()
