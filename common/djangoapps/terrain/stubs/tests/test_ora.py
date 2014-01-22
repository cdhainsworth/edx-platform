"""
Unit tests for stub ORA implementation.
"""

import unittest
import requests
from ..ora import StubOraService, StubOraHandler, StudentState


class StubOraServiceTest(unittest.TestCase):

    def setUp(self):
        """
        Start the stub server.
        """
        self.server = StubOraService()
        self.addCleanup(self.server.shutdown)

    def test_calibration(self):

        # Ensure that we use the same student ID throughout
        student_id = '1234'

        # Initially, student should not be calibrated
        response = requests.get(
            self._peer_url('is_student_calibrated'),
            params={'student_id': student_id, 'problem_id': '5678'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'total_calibrated_on_so_far': 0,
            'calibrated': False
        })

        # Retrieve a calibration essay
        response = requests.get(
            self._peer_url('show_calibration_essay'),
            params={'student_id': student_id, 'problem_id': '5678'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'submission_id': self.server.DUMMY_DATA['submission_id'],
            'submission_key': self.server.DUMMY_DATA['submission_key'],
            'student_response': self.server.DUMMY_DATA['student_response'],
            'prompt': self.server.DUMMY_DATA['prompt'],
            'rubric': self.server.DUMMY_DATA['rubric'],
            'max_score': self.server.DUMMY_DATA['max_score']
        })

        # Grade the calibration essay
        response = requests.post(
            self._peer_url('save_calibration_essay'),
            data={
                'student_id': student_id,
                'location': 'test location',
                'calibration_essay_id': 1,
                'score': 2,
                'submission_key': 'key',
                'feedback': 'Good job!'
            }
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'message': self.server.DUMMY_DATA['message'],
            'actual_score': self.server.DUMMY_DATA['actual_score'],
            'actual_rubric': self.server.DUMMY_DATA['actual_rubric'],
            'actual_feedback': self.server.DUMMY_DATA['actual_feedback']
        })

        # Now the student should be calibrated
        response = requests.get(
            self._peer_url('is_student_calibrated'),
            params={'student_id': student_id, 'problem_id': '5678'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'total_calibrated_on_so_far': 1,
            'calibrated': True
        })

        # But a student with a different ID should NOT be calibrated.
        response = requests.get(
            self._peer_url('is_student_calibrated'),
            params={'student_id': 'another', 'problem_id': '5678'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'total_calibrated_on_so_far': 0,
            'calibrated': False
        })

    def test_grade_peers(self):

        # Ensure a consistent student ID
        student_id = '1234'

        # Check initial number of submissions
        # Should be none graded and 1 required
        self._assert_num_graded(student_id, 0, 1)

        # Retrieve the next submission
        response = requests.get(
            self._peer_url('get_next_submission'),
            params={'grader_id': student_id, 'location': 'test'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'submission_id': self.server.DUMMY_DATA['submission_id'],
            'submission_key': self.server.DUMMY_DATA['submission_key'],
            'prompt': self.server.DUMMY_DATA['prompt'],
            'rubric': self.server.DUMMY_DATA['rubric'],
            'max_score': self.server.DUMMY_DATA['max_score']
        })

        # Grade the submission
        response = requests.post(
            self._peer_url('save_grade'),
            data={
                'location': 'test',
                'grader_id': student_id,
                'submission_id': 1,
                'score': 2,
                'feedback': 'Good job!',
                'submission_key': 'key'
            }
        )
        self._assert_response(response, {'version': 1, 'success': True})

        # Check final number of submissions
        # Shoud be one graded  and none required
        self._assert_num_graded(student_id, 1, 0)

        # Grade the next submission the submission
        response = requests.post(
            self._peer_url('save_grade'),
            data={
                'location': 'test',
                'grader_id': student_id,
                'submission_id': 1,
                'score': 2,
                'feedback': 'Good job!',
                'submission_key': 'key'
            }
        )
        self._assert_response(response, {'version': 1, 'success': True})

        # Check final number of submissions
        # Shoud be two graded  and none required
        self._assert_num_graded(student_id, 2, 0)

    def test_problem_list(self):

        # The problem list returns dummy counts which are not updated
        # The location we use is ignored by the LMS, and we ignore it in the stub,
        # so we use a dummy value there too.
        response = requests.get(
            self._peer_url('get_problem_list'),
            params={'course_id': 'test course'}
        )

        self._assert_response(response, {
            'version': 1, 'success': True,
            'problem_list': self.server.DUMMY_DATA['problem_list']
        })


    def _peer_url(self, path):
        """
        Construt a URL to the stub ORA peer-grading service.
        """
        return "http://127.0.0.1:{port}/peer_grading/{path}/".format(
            port=self.server.port, path=path
        )

    def _assert_response(self, response, expected_json):
        """
        Assert that the `response` was successful and contained
        `expected_json` (dict) as its content.
        """
        self.assertTrue(response.ok)
        self.assertEqual(response.json(), expected_json)

    def _assert_num_graded(self, student_id, num_graded, num_required):
        """
        ORA provides two distinct ways to get the submitted/graded counts.
        Here we check both of them to ensure that the number that we've graded
        is consistently `num_graded`.
        """

        # Unlike the actual ORA service,
        # we keep track of counts on a per-student basis.
        # This means that every user starts with N essays to grade,
        # and as they grade essays, that number decreases.
        # We do NOT simulate students adding more essays to the queue,
        # and essays that the current student submits are NOT graded
        # by other students.
        num_pending = StudentState.INITIAL_ESSAYS_AVAILABLE - num_graded

        # Notifications
        response = requests.get(
            self._peer_url('get_notifications'),
            params={'student_id': student_id, 'course_id': 'test course'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'count_required': num_required,
            'student_sub_count': self.server.DUMMY_DATA['student_sub_count'],
            'count_graded': num_graded,
            'count_available': num_pending
        })

        # Location data
        response = requests.get(
            self._peer_url('get_data_for_location'),
            params={'location': 'test location', 'student_id': student_id}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'count_required': num_required,
            'student_sub_count': self.server.DUMMY_DATA['student_sub_count'],
            'count_graded': num_graded,
            'count_available': num_pending
        })
