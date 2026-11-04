import unittest
from evaluate_counts import evaluate


class CountEvaluationTests(unittest.TestCase):
    def test_errors_are_computed_against_humans(self):
        result = evaluate({'result': {'samples': [{'frame': 0, 'people': 3}, {'frame': 5, 'people': 10}]}},
                          {'samples': [{'frame': 0, 'people': 5}, {'frame': 5, 'people': 6}]})
        self.assertEqual(result['mean_absolute_error'], 3)
        self.assertEqual(result['max_absolute_error'], 4)
        self.assertEqual(result['frames_outside_plus_minus_2'], 1)
        self.assertFalse(result['within_plus_minus_2_on_annotated_frames'])

    def test_missing_duplicate_unknown_and_mismatched_labels_fail(self):
        export = {'id': 'one', 'result': {'samples': [{'frame': 0, 'people': 1}]}}
        for labels in [{'samples': []}, {'analysis_id': 'two', 'samples': [{'frame': 0, 'people': 1}]},
                       {'samples': [{'frame': 2, 'people': 1}]}, {'samples': [{'frame': 0, 'people': True}]},
                       {'samples': [{'frame': 0, 'people': 1}, {'frame': 0, 'people': 2}]}]:
            with self.assertRaises(ValueError):
                evaluate(export, labels)
