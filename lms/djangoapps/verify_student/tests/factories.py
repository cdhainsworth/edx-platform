from verify_student.models import MidcourseReverificationWindow
from factory.django import DjangoModelFactory
import pytz
from datetime import timedelta, datetime


# Factories don't have __init__ methods, and are self documenting
# pylint: disable=W0232
class MidcourseReverificationWindowFactory(DjangoModelFactory):
    FACTORY_FOR = MidcourseReverificationWindow

    course_id = u'MITx/999/Robot_Super_Course'
    start_date = datetime.now(pytz.UTC) - timedelta(days=100)
    end_date = datetime.now(pytz.UTC) + timedelta(days=100)
