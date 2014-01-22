"""
Stub implementation of ORA service.

This is an extremely simple version of the service, with most
business logic removed.  In particular, the stub:

1) Provides an infinite number of peer and calibration essays,
   with dummy data.

2) Simulates a set number of pending submissions for each student;
   grades submitted by one student are not used for any other student.

3) Ignores the scores/feedback students submit.

4) Ignores problem location: an essay graded for *any* problem is graded
   for *every* problem.

Basically, the stub tracks only the *number* of peer/calibration essays
submitted by each student.
"""

import json
import pkg_resources
from .http import StubHttpRequestHandler, StubHttpService, require_params


class StudentState(object):
    """
    Store state about the student that the stub
    ORA implementation needs to keep track of.
    """
    INITIAL_ESSAYS_AVAILABLE = 3
    NUM_ESSAYS_REQUIRED = 1
    NUM_CALIBRATION_REQUIRED = 1

    def __init__(self):
        self.num_graded = 0
        self.num_calibrated = 0

    def grade_peer_essay(self):
        self.num_graded += 1

    def grade_calibration_essay(self):
        self.num_calibrated += 1

    @property
    def num_pending(self):
        return max(self.INITIAL_ESSAYS_AVAILABLE- self.num_graded, 0)

    @property
    def num_required(self):
        return max(self.NUM_ESSAYS_REQUIRED - self.num_graded, 0)

    @property
    def is_calibrated(self):
        return self.num_calibrated >= self.NUM_CALIBRATION_REQUIRED


class StubOraHandler(StubHttpRequestHandler):
    """
    Handler for ORA requests.
    """

    GET_URL_HANDLERS = {
        '/peer_grading/get_next_submission': '_get_next_submission',
        '/peer_grading/is_student_calibrated': '_is_student_calibrated',
        '/peer_grading/show_calibration_essay': '_show_calibration_essay',
        '/peer_grading/get_notifications': '_get_notifications',
        '/peer_grading/get_data_for_location': '_get_data_for_location',
        '/peer_grading/get_problem_list': '_get_problem_list',
    }

    POST_URL_HANDLERS = {
        '/peer_grading/save_grade': '_save_grade',
        '/peer_grading/save_calibration_essay': '_save_calibration_essay',
    }

    def do_GET(self):
        """
        Handle GET methods to the ORA API stub.
        """
        self._send_handler_response('GET')

    def do_POST(self):
        """
        Handle POST methods to the ORA API stub.
        """
        self._send_handler_response('POST')

    def _send_handler_response(self, method):
        """
        Delegate response to handler methods.
        If no handler defined, send a 404 response.
        """
        # Choose the list of handlers based on the HTTP method
        if method == 'GET':
            handler_list = self.GET_URL_HANDLERS
        elif method == 'POST':
            handler_list = self.POST_URL_HANDLERS
        else:
            self.log_error('Unrecognized method "{method}"'.format(method=method))
            return

        # Check the path (without querystring params) against our list of handlers
        handler_name = handler_list.get(self.path_only)

        if handler_name is not None:
            handler = getattr(self, handler_name, None)
        else:
            handler = None

        # Delegate to the handler to send a response
        if handler is not None:
            handler()

        # If we don't have a handler for this URL and/or HTTP method,
        # respond with a 404.  This is the same behavior as the ORA API.
        else:
            self.send_response(404)

    @require_params('GET', 'student_id', 'problem_id')
    def _is_student_calibrated(self):
        """
        Query whether the student has completed enough calibration
        essays to begin peer grading.

        Method: GET

        Params:
            - student_id
            - problem_id

        Result (JSON):
            - success (bool)
            - total_calibrated_on_so_far (int)
            - calibrated (bool)
        """
        student = self._student('GET')
        if student is None:
            self._error_response()

        else:
            self._success_response({
                'total_calibrated_on_so_far': student.num_calibrated,
                'calibrated': student.is_calibrated
            })

    @require_params('GET', 'student_id', 'problem_id')
    def _show_calibration_essay(self):
        """
        Retrieve a calibration essay for the student to grade.

        Method: GET

        Params:
            - student_id
            - problem_id

        Result (JSON):
            - success (bool)
            - submission_id (str)
            - submission_key (str)
            - student_response (str)
            - prompt (str)
            - rubric (str)
            - max_score (int)
        """
        self._success_response({
            'submission_id': self.server.DUMMY_DATA['submission_id'],
            'submission_key': self.server.DUMMY_DATA['submission_key'],
            'student_response': self.server.DUMMY_DATA['student_response'],
            'prompt': self.server.DUMMY_DATA['prompt'],
            'rubric': self.server.DUMMY_DATA['rubric'],
            'max_score': self.server.DUMMY_DATA['max_score']
        })

    @require_params('GET', 'student_id', 'course_id')
    def _get_notifications(self):
        """
        Query counts of submitted, required, graded, and available peer essays
        for a particular student.

        Method: GET

        Params:
            - student_id
            - course_id

        Result (JSON):
            - success (bool)
            - student_sub_count (int)
            - count_required (int)
            - count_graded (int)
            - count_available (int)
        """
        student = self._student('GET')
        if student is None:
            self._error_response()

        else:
            self._success_response({
                'student_sub_count': self.server.DUMMY_DATA['student_sub_count'],
                'count_required': student.num_required,
                'count_graded': student.num_graded,
                'count_available': student.num_pending
            })

    @require_params('GET', 'student_id', 'location')
    def _get_data_for_location(self):
        """
        Query counts of submitted, required, graded, and available peer essays
        for a problem location.

        Method: GET

        Params:
            - student_id
            - location

        Result (JSON):
            - success (bool)
            - student_sub_count (int)
            - count_required (int)
            - count_graded (int)
            - count_available (int)
        """
        student = self._student('GET')
        if student is None:
            self._error_response()

        else:
            self._success_response({
                'student_sub_count': self.server.DUMMY_DATA['student_sub_count'],
                'count_required': student.num_required,
                'count_graded': student.num_graded,
                'count_available': student.num_pending
            })

    @require_params('GET', 'grader_id', 'location')
    def _get_next_submission(self):
        """
        Retrieve the next submission for the student to peer-grade.

        Method: GET

        Params:
            - grader_id
            - location

        Result (JSON):
            - success (bool)
            - submission_id (str)
            - submission_key (str)
            - prompt (str, HTML)
            - rubric (str, XML)
            - max_score (int)
        """
        self._success_response({
            'submission_id': self.server.DUMMY_DATA['submission_id'],
            'submission_key': self.server.DUMMY_DATA['submission_key'],
            'prompt': self.server.DUMMY_DATA['prompt'],
            'rubric': self.server.DUMMY_DATA['rubric'],
            'max_score': self.server.DUMMY_DATA['max_score']
        })

    @require_params('GET', 'course_id')
    def _get_problem_list(self):
        """
        Retrieve the list of problems available for peer grading.

        Method: GET

        Params:
            - course_id

        Result (JSON):
            - success (bool)
            - problem_list (list)

        where `problem_list` is a list of dictionaries with keys:
            - location (str)
            - problem_name (str)
            - num_graded (int)
            - num_pending (int)
        """
        self._success_response({'problem_list': self.server.DUMMY_DATA['problem_list']})


    @require_params('POST', 'grader_id', 'location', 'submission_id', 'score', 'feedback', 'submission_key')
    def _save_grade(self):
        """
        Save a score and feedback for an essay the student has graded.

        Method: POST

        Params:
            - grader_id
            - location
            - submission_id
            - score
            - feedback
            - submission_key

        Result (JSON):
            - success (bool)
        """
        student = self._student('POST', key='grader_id')
        if student is None:
            self._error_response()

        else:
            # Update the number of essays the student has graded
            student.grade_peer_essay()
            return self._success_response({})

    @require_params('POST', 'student_id', 'location', 'calibration_essay_id', 'score', 'feedback', 'submission_key')
    def _save_calibration_essay(self):
        """
        Save a score and feedback for a calibration essay the student has graded.
        Returns the scores/feedback that the instructor gave for the essay.

        Method: POST

        Params:
            - student_id
            - location
            - calibration_essay_id
            - score
            - feedback
            - submission_key

        Result (JSON):
            - success (bool)
            - message (str)
            - actual_score (int)
            - actual_rubric (str, XML)
            - actual_feedback (str)
        """
        student = self._student('POST')
        if student is None:
            self._error_response()

        else:

            # Increment the student calibration count
            student.grade_calibration_essay()

            self._success_response({
                'message': self.server.DUMMY_DATA['message'],
                'actual_score': self.server.DUMMY_DATA['actual_score'],
                'actual_rubric': self.server.DUMMY_DATA['actual_rubric'],
                'actual_feedback': self.server.DUMMY_DATA['actual_feedback']
            })

    def _student(self, method, key='student_id'):
        """
        Return the `StudentState` instance for the student ID given
        in the request parameters.

        `method` is the HTTP request method (either "GET" or "POST")
        and `key` is the parameter key.
        """
        if method == 'GET':
            student_id = self.get_params.get(key)
        elif method == 'POST':
            student_id = self.post_dict.get(key)
        else:
            self.log_error("Unrecognized method '{method}'".format(method=method))
            return None

        if student_id is None:
            self.log_error("Could not get student ID from parameters")
            return None

        return self.server.student_state(student_id)

    def _success_response(self, response_dict):
        """
        Send a success response.
        `response_dict` is a Python dictionary to JSON-encode.
        """
        response_dict['success'] = True
        response_dict['version'] = 1
        self.send_response(
            200, content=json.dumps(response_dict),
            headers={'Content-type': 'application/json'}
        )

    def _error_response(self):
        """
        Send an error response.
        """
        response_dict = {'success': False, 'version': 1}
        self.send_response(
            400, content=json.dumps(response_dict),
            headers={'Content-type': 'application/json'}
        )


class StubOraService(StubHttpService):
    """
    Stub ORA service.
    """
    HANDLER_CLASS = StubOraHandler

    DUMMY_DATA = {
        'submission_id': 1,
        'submission_key': 'test key',
        'student_response': 'Test response',
        'prompt': 'Test prompt',
        'rubric': pkg_resources.resource_string(__name__, "data/ora_rubric.xml"),
        'max_score': 2,
        'message': 'Successfully saved calibration record.',
        'actual_score': 2,
        'actual_rubric': pkg_resources.resource_string(__name__, "data/ora_graded_rubric.xml"),
        'actual_feedback': 'Great job!',
        'student_sub_count': 1,
        'problem_list': [{
            'location': 'test_location',
            'problem_name': 'test problem',
            'num_graded': 1,
            'num_pending': 1,
        }],
    }

    def __init__(self, *args, **kwargs):
        """
        Initialize student submission state.
        """
        super(StubOraService, self).__init__(*args, **kwargs)

        # Create a dict to map student ID's to their state
        self._students = dict()

    def student_state(self, student_id):
        """
        Return the `StudentState` (named tuple) for the student
        with ID `student_id`.  The student state can be modified by the caller.
        """
        # Create the student state if it does not already exist
        if student_id not in self._students:
            student = StudentState()
            self._students[student_id] = student

        # Retrieve the student state
        return self._students[student_id]
