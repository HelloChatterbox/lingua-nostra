#
# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest
from datetime import datetime, timedelta

from lingua_nostra import load_language, unload_language, set_default_lang
from lingua_nostra.internal import FunctionNotLocalizedError
from lingua_nostra.time import default_timezone
from lingua_nostra.parse import extract_datetime
from lingua_nostra.parse import extract_duration
from lingua_nostra.parse import extract_number, extract_numbers
from lingua_nostra.parse import fuzzy_match
from lingua_nostra.parse import get_gender
from lingua_nostra.parse import match_one
from lingua_nostra.parse import normalize
from lingua_nostra.parse import extract_quantities
from lingua_nostra.parse import extract_entities, EntityType, extract_query, \
    predict_question_type
from lingua_nostra.lang.parse_common import QuestionSubType


def setUpModule():
    # TODO spin off English tests
    load_language('en')
    set_default_lang('en')


def tearDownModule():
    unload_language('en')


class TestFuzzyMatch(unittest.TestCase):
    def test_matches(self):
        self.assertTrue(fuzzy_match("you and me", "you and me") >= 1.0)
        self.assertTrue(fuzzy_match("you and me", "you") < 0.5)
        self.assertTrue(fuzzy_match("You", "you") > 0.5)
        self.assertTrue(fuzzy_match("you and me", "you") ==
                        fuzzy_match("you", "you and me"))
        self.assertTrue(fuzzy_match("you and me", "he or they") < 0.2)

    def test_match_one(self):
        # test list of choices
        choices = ['frank', 'kate', 'harry', 'henry']
        self.assertEqual(match_one('frank', choices)[0], 'frank')
        self.assertEqual(match_one('fran', choices)[0], 'frank')
        self.assertEqual(match_one('enry', choices)[0], 'henry')
        self.assertEqual(match_one('katt', choices)[0], 'kate')
        # test dictionary of choices
        choices = {'frank': 1, 'kate': 2, 'harry': 3, 'henry': 4}
        self.assertEqual(match_one('frank', choices)[0], 1)
        self.assertEqual(match_one('enry', choices)[0], 4)


class TestNormalize(unittest.TestCase):
    def test_articles(self):
        self.assertEqual(normalize("this is a test", remove_articles=True),
                         "this is test")
        self.assertEqual(normalize("this is the test", remove_articles=True),
                         "this is test")
        self.assertEqual(normalize("and another test", remove_articles=True),
                         "and another test")
        self.assertEqual(normalize("this is an extra test",
                                   remove_articles=False),
                         "this is an extra test")

    def test_extract_number_decimal_markers(self):
        # Test decimal normalization
        self.assertEqual(extract_number("4,4", decimal=','), 4.4)
        self.assertEqual(extract_number("we have 3,5 kilometers to go",
                                        decimal=','), 3.5)
        self.assertEqual(extract_numbers("this is a seven eight 9,5 test",
                                         decimal=','),
                         [7.0, 8.0, 9.5])
        self.assertEqual(extract_numbers("this is a 7,0 8.0 9,6 test",
                                         decimal=','), [7.0, 8.0, 9.6])

    def test_extract_number_priority(self):
        # sanity check
        self.assertEqual(extract_number("third", ordinals=True), 3)
        self.assertEqual(extract_number("sixth", ordinals=True), 6)

        # TODO a suite of tests needs to be written depending on outcome of
        #  https://github.com/MycroftAI/lingua-franca/issues/152
        # the tests bellow are flagged as problematic, some of those ARE BROKEN
        # for now this is considered undefined behaviour!!!

        # NOTE this test is returning the first number, which seems to be
        # the consensus regarding correct behaviour
        self.assertEqual(extract_number("Twenty two and Three Fifths",
                                        ordinals=True), 22)

        # TODO these should return the 1st number, not the last, ordinals
        #  seem messed up, the rest of the codebase is returning first
        #  number most likely tests bellow are bugs, i repeat, tests bellow
        #  are testing FOR THE "WRONG" VALUE
        self.assertEqual(extract_number("sixth third", ordinals=True), 3)
        self.assertEqual(extract_number("third sixth", ordinals=True), 6)

    def test_extract_number_ambiguous(self):
        # test explicit ordinals
        self.assertEqual(extract_number("this is the 1st",
                                        ordinals=True), 1)
        self.assertEqual(extract_number("this is the 2nd",
                                        ordinals=False), 2)
        self.assertEqual(extract_number("this is the 3rd",
                                        ordinals=None), 3)
        self.assertEqual(extract_number("this is the 4th",
                                        ordinals=None), 4)
        self.assertEqual(extract_number(
            "this is the 7th test", ordinals=True), 7)
        self.assertEqual(extract_number(
            "this is the 7th test", ordinals=False), 7)
        self.assertTrue(extract_number("this is the nth test") is False)
        self.assertEqual(extract_number("this is the 1st test"), 1)
        self.assertEqual(extract_number("this is the 2nd test"), 2)
        self.assertEqual(extract_number("this is the 3rd test"), 3)
        self.assertEqual(extract_number("this is the 31st test"), 31)
        self.assertEqual(extract_number("this is the 32nd test"), 32)
        self.assertEqual(extract_number("this is the 33rd test"), 33)
        self.assertEqual(extract_number("this is the 34th test"), 34)

        # test non ambiguous ordinals
        self.assertEqual(extract_number("this is the first test",
                                        ordinals=True), 1)
        self.assertEqual(extract_number("this is the first test",
                                        ordinals=False), False)
        self.assertEqual(extract_number("this is the first test",
                                        ordinals=None), False)

        # test ambiguous ordinal/time unit
        self.assertEqual(extract_number("this is second test",
                                        ordinals=True), 2)
        self.assertEqual(extract_number("this is second test",
                                        ordinals=False), False)
        self.assertEqual(extract_number("remind me in a second",
                                        ordinals=True), 2)
        self.assertEqual(extract_number("remind me in a second",
                                        ordinals=False), False)
        self.assertEqual(extract_number("remind me in a second",
                                        ordinals=None), False)

        # test ambiguous ordinal/fractional
        self.assertEqual(extract_number("this is the third test",
                                        ordinals=True), 3.0)
        self.assertEqual(extract_number("this is the third test",
                                        ordinals=False), 1.0 / 3.0)
        self.assertEqual(extract_number("this is the third test",
                                        ordinals=None), False)

        self.assertEqual(extract_number("one third of a cup",
                                        ordinals=False), 1.0 / 3.0)
        self.assertEqual(extract_number("one third of a cup",
                                        ordinals=True), 3)
        self.assertEqual(extract_number("one third of a cup",
                                        ordinals=None), 1)

        # test plurals
        # NOTE plurals are never considered ordinals, but also not
        # considered explicit fractions
        self.assertEqual(extract_number("2 fifths",
                                        ordinals=True), 2)
        self.assertEqual(extract_number("2 fifth",
                                        ordinals=True), 5)
        self.assertEqual(extract_number("2 fifths",
                                        ordinals=False), 2 / 5)
        self.assertEqual(extract_number("2 fifths",
                                        ordinals=None), 2)

        self.assertEqual(extract_number("Twenty two and Three Fifths"), 22.6)

        # test multiple ambiguous
        self.assertEqual(extract_number("sixth third", ordinals=None), False)
        self.assertEqual(extract_number("thirty second", ordinals=False), 30)
        self.assertEqual(extract_number("thirty second", ordinals=None), 30)
        self.assertEqual(extract_number("thirty second", ordinals=True), 32)
        # TODO this test is imperfect, further discussion needed
        # "Sixth third" would probably refer to "the sixth instance of a third"
        # I dunno what should be returned here, don't think it should be cumulative.
        self.assertEqual(extract_number("sixth third", ordinals=False),
                         1 / 6 / 3)

        # test big numbers / short vs long scale
        self.assertEqual(extract_number("this is the billionth test",
                                        ordinals=True), 1e09)
        self.assertEqual(extract_number("this is the billionth test",
                                        ordinals=None), False)

        self.assertEqual(extract_number("this is the billionth test",
                                        ordinals=False), 1e-9)
        self.assertEqual(extract_number("this is the billionth test",
                                        ordinals=True,
                                        short_scale=False), 1e12)
        self.assertEqual(extract_number("this is the billionth test",
                                        ordinals=None,
                                        short_scale=False), False)
        self.assertEqual(extract_number("this is the billionth test",
                                        short_scale=False), 1e-12)

        # test the Nth one
        self.assertEqual(extract_number("the fourth one", ordinals=True), 4.0)
        self.assertEqual(extract_number("the thirty sixth one",
                                        ordinals=True), 36.0)
        self.assertEqual(extract_number(
            "you are the second one", ordinals=False), 1)
        self.assertEqual(extract_number(
            "you are the second one", ordinals=True), 2)
        self.assertEqual(extract_number("you are the 1st one",
                                        ordinals=None), 1)
        self.assertEqual(extract_number("you are the 2nd one",
                                        ordinals=None), 2)
        self.assertEqual(extract_number("you are the 3rd one",
                                        ordinals=None), 3)
        self.assertEqual(extract_number("you are the 8th one",
                                        ordinals=None), 8)

    def test_extract_number(self):
        self.assertEqual(extract_number("this is 2 test"), 2)
        self.assertEqual(extract_number("this is test number 4"), 4)
        self.assertEqual(extract_number("three cups"), 3)
        self.assertEqual(extract_number("1/3 cups"), 1.0 / 3.0)
        self.assertEqual(extract_number("quarter cup"), 0.25)
        self.assertEqual(extract_number("1/4 cup"), 0.25)
        self.assertEqual(extract_number("one fourth cup"), 0.25)
        self.assertEqual(extract_number("2/3 cups"), 2.0 / 3.0)
        self.assertEqual(extract_number("3/4 cups"), 3.0 / 4.0)
        self.assertEqual(extract_number("1 and 3/4 cups"), 1.75)
        self.assertEqual(extract_number("1 cup and a half"), 1.5)
        self.assertEqual(extract_number("one cup and a half"), 1.5)
        self.assertEqual(extract_number("one and a half cups"), 1.5)
        self.assertEqual(extract_number("one and one half cups"), 1.5)
        self.assertEqual(extract_number("three quarter cups"), 3.0 / 4.0)
        self.assertEqual(extract_number("three quarters cups"), 3.0 / 4.0)
        self.assertEqual(extract_number("twenty two"), 22)
        self.assertEqual(extract_number(
            "Twenty two with a leading capital letter"), 22)
        self.assertEqual(extract_number(
            "twenty Two with Two capital letters"), 22)
        self.assertEqual(extract_number(
            "twenty Two with mixed capital letters"), 22)
        self.assertEqual(extract_number("two hundred"), 200)
        self.assertEqual(extract_number("nine thousand"), 9000)
        self.assertEqual(extract_number("six hundred sixty six"), 666)
        self.assertEqual(extract_number("two million"), 2000000)
        self.assertEqual(extract_number("two million five hundred thousand "
                                        "tons of spinning metal"), 2500000)
        self.assertEqual(extract_number("six trillion"), 6000000000000.0)
        self.assertEqual(extract_number("six trillion", short_scale=False),
                         6e+18)
        self.assertEqual(extract_number("one point five"), 1.5)
        self.assertEqual(extract_number("three dot fourteen"), 3.14)
        self.assertEqual(extract_number("zero point two"), 0.2)
        self.assertEqual(extract_number("billions of years older"),
                         1000000000.0)
        self.assertEqual(extract_number("billions of years older",
                                        short_scale=False),
                         1000000000000.0)
        self.assertEqual(extract_number("one hundred thousand"), 100000)
        self.assertEqual(extract_number("minus 2"), -2)
        self.assertEqual(extract_number("negative seventy"), -70)
        self.assertEqual(extract_number("thousand million"), 1000000000)

        # Verify non-power multiples of ten no longer discard
        # adjacent multipliers
        self.assertEqual(extract_number("twenty thousand"), 20000)
        self.assertEqual(extract_number("fifty million"), 50000000)

        # Verify smaller powers of ten no longer cause miscalculation of larger
        # powers of ten (see MycroftAI#86)
        self.assertEqual(extract_number("twenty billion three hundred million \
                                        nine hundred fifty thousand six hundred \
                                        seventy five point eight"),
                         20300950675.8)
        self.assertEqual(extract_number("nine hundred ninety nine million nine \
                                        hundred ninety nine thousand nine \
                                        hundred ninety nine point nine"),
                         999999999.9)

        # TODO why does "trillion" result in xxxx.0?
        self.assertEqual(extract_number("eight hundred trillion two hundred \
                                        fifty seven"), 800000000000257.0)

        # TODO handle this case
        # self.assertEqual(
        #    extract_number("6 dot six six six"),
        #    6.666)
        self.assertTrue(extract_number("The tennis player is fast") is False)
        self.assertTrue(extract_number("fraggle") is False)

        self.assertTrue(extract_number("fraggle zero") is not False)
        self.assertEqual(extract_number("fraggle zero"), 0)

        self.assertTrue(extract_number("grobo 0") is not False)
        self.assertEqual(extract_number("grobo 0"), 0)

        self.assertEqual(extract_number("a couple of beers"), 2)
        self.assertEqual(extract_number("a couple hundred beers"), 200)
        self.assertEqual(extract_number("a couple thousand beers"), 2000)
        self.assertEqual(extract_number("totally 100%"), 100)

    def test_extract_duration_en(self):
        self.assertEqual(extract_duration("10 seconds"),
                         (timedelta(seconds=10.0), ""))
        self.assertEqual(extract_duration("5 minutes"),
                         (timedelta(minutes=5), ""))
        self.assertEqual(extract_duration("2 hours"),
                         (timedelta(hours=2), ""))
        self.assertEqual(extract_duration("3 days"),
                         (timedelta(days=3), ""))
        self.assertEqual(extract_duration("25 weeks"),
                         (timedelta(weeks=25), ""))
        self.assertEqual(extract_duration("seven hours"),
                         (timedelta(hours=7), ""))
        self.assertEqual(extract_duration("7.5 seconds"),
                         (timedelta(seconds=7.5), ""))
        self.assertEqual(extract_duration("eight and a half days thirty"
                                          " nine seconds"),
                         (timedelta(days=8.5, seconds=39), ""))
        self.assertEqual(extract_duration("wake me up in three weeks, four"
                                          " hundred ninety seven days, and"
                                          " three hundred 91.6 seconds"),
                         (timedelta(weeks=3, days=497, seconds=391.6),
                          "wake me up in , , and"))
        self.assertEqual(extract_duration("10-seconds"),
                         (timedelta(seconds=10.0), ""))
        self.assertEqual(extract_duration("5-minutes"),
                         (timedelta(minutes=5), ""))

    def test_extract_duration_case_en(self):
        self.assertEqual(extract_duration("Set a timer for 30 minutes"),
                         (timedelta(minutes=30), "Set a timer for"))
        self.assertEqual(extract_duration("The movie is one hour, fifty seven"
                                          " and a half minutes long"),
                         (timedelta(hours=1, minutes=57.5),
                          "The movie is ,  long"))
        self.assertEqual(extract_duration("Four and a Half minutes until"
                                          " sunset"),
                         (timedelta(minutes=4.5), "until sunset"))
        self.assertEqual(extract_duration("Nineteen minutes past THE hour"),
                         (timedelta(minutes=19), "past THE hour"))

    def test_extractdatetime_fractions_en(self):
        def extractWithFormat(text):
            date = datetime(2017, 6, 27, 13, 4,
                            tzinfo=default_timezone())  # Tue June 27, 2017 @ 1:04pm
            [extractedDate, leftover] = extract_datetime(text, date)
            extractedDate = extractedDate.strftime("%Y-%m-%d %H:%M:%S")
            return [extractedDate, leftover]

        def testExtract(text, expected_date, expected_leftover):
            res = extractWithFormat(normalize(text))
            self.assertEqual(res[0], expected_date, "for=" + text)
            self.assertEqual(res[1], expected_leftover, "for=" + text)

        testExtract("Set the ambush for half an hour",
                    "2017-06-27 13:34:00", "set ambush")
        testExtract("remind me to call mom in half an hour",
                    "2017-06-27 13:34:00", "remind me to call mom")
        testExtract("remind me to call mom in a half hour",
                    "2017-06-27 13:34:00", "remind me to call mom")
        testExtract("remind me to call mom in a quarter hour",
                    "2017-06-27 13:19:00", "remind me to call mom")
        testExtract("remind me to call mom in a quarter of an hour",
                    "2017-06-27 13:19:00", "remind me to call mom")

    def test_extractdatetime_en(self):
        def extractWithFormat(text):
            date = datetime(2017, 6, 27, 13, 4,
                            tzinfo=default_timezone())  # Tue June 27, 2017 @ 1:04pm
            [extractedDate, leftover] = extract_datetime(text, date)
            extractedDate = extractedDate.strftime("%Y-%m-%d %H:%M:%S")
            return [extractedDate, leftover]

        def testExtract(text, expected_date, expected_leftover):
            res = extractWithFormat(normalize(text))
            self.assertEqual(res[0], expected_date, "for=" + text)
            self.assertEqual(res[1], expected_leftover, "for=" + text)

        testExtract("now is the time",
                    "2017-06-27 13:04:00", "is time")
        testExtract("in a second",
                    "2017-06-27 13:04:01", "")
        testExtract("in a minute",
                    "2017-06-27 13:05:00", "")
        testExtract("in a couple minutes",
                    "2017-06-27 13:06:00", "")
        testExtract("in a couple of minutes",
                    "2017-06-27 13:06:00", "")
        testExtract("in a couple hours",
                    "2017-06-27 15:04:00", "")
        testExtract("in a couple of hours",
                    "2017-06-27 15:04:00", "")
        testExtract("in a couple weeks",
                    "2017-07-11 00:00:00", "")
        testExtract("in a couple of weeks",
                    "2017-07-11 00:00:00", "")
        testExtract("in a couple months",
                    "2017-08-27 00:00:00", "")
        testExtract("in a couple years",
                    "2019-06-27 00:00:00", "")
        testExtract("in a couple of months",
                    "2017-08-27 00:00:00", "")
        testExtract("in a couple of years",
                    "2019-06-27 00:00:00", "")
        testExtract("in a decade",
                    "2027-06-27 00:00:00", "")
        testExtract("in a couple of decades",
                    "2037-06-27 00:00:00", "")
        testExtract("next decade",
                    "2027-06-27 00:00:00", "")
        testExtract("in a century",
                    "2117-06-27 00:00:00", "")
        testExtract("in a millennium",
                    "3017-06-27 00:00:00", "")
        testExtract("in a couple decades",
                    "2037-06-27 00:00:00", "")
        testExtract("in 5 decades",
                    "2067-06-27 00:00:00", "")
        testExtract("in a couple centuries",
                    "2217-06-27 00:00:00", "")
        testExtract("in a couple of centuries",
                    "2217-06-27 00:00:00", "")
        testExtract("in 2 centuries",
                    "2217-06-27 00:00:00", "")
        testExtract("in a couple millenniums",
                    "4017-06-27 00:00:00", "")
        testExtract("in a couple of millenniums",
                    "4017-06-27 00:00:00", "")
        testExtract("in an hour",
                    "2017-06-27 14:04:00", "")
        testExtract("i want it within the hour",
                    "2017-06-27 14:04:00", "i want it")
        testExtract("in 1 second",
                    "2017-06-27 13:04:01", "")
        testExtract("in 2 seconds",
                    "2017-06-27 13:04:02", "")
        testExtract("Set the ambush in 1 minute",
                    "2017-06-27 13:05:00", "set ambush")
        testExtract("Set the ambush for 5 days from today",
                    "2017-07-02 00:00:00", "set ambush")
        testExtract("day after tomorrow",
                    "2017-06-29 00:00:00", "")
        testExtract("What is the day after tomorrow's weather?",
                    "2017-06-29 00:00:00", "what is weather")
        testExtract("Remind me at 10:45 pm",
                    "2017-06-27 22:45:00", "remind me")
        testExtract("what is the weather on friday morning",
                    "2017-06-30 08:00:00", "what is weather")
        testExtract("what is tomorrow's weather",
                    "2017-06-28 00:00:00", "what is weather")
        testExtract("what is this afternoon's weather",
                    "2017-06-27 15:00:00", "what is weather")
        testExtract("what is this evening's weather",
                    "2017-06-27 19:00:00", "what is weather")
        testExtract("what was this morning's weather",
                    "2017-06-27 08:00:00", "what was weather")
        testExtract("remind me to call mom in 8 weeks and 2 days",
                    "2017-08-24 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom on august 3rd",
                    "2017-08-03 00:00:00", "remind me to call mom")
        testExtract("remind me tomorrow to call mom at 7am",
                    "2017-06-28 07:00:00", "remind me to call mom")
        testExtract("remind me tomorrow to call mom at 10pm",
                    "2017-06-28 22:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 7am",
                    "2017-06-28 07:00:00", "remind me to call mom")
        testExtract("remind me to call mom in an hour",
                    "2017-06-27 14:04:00", "remind me to call mom")
        testExtract("remind me to call mom at 1730",
                    "2017-06-27 17:30:00", "remind me to call mom")
        testExtract("remind me to call mom at 0630",
                    "2017-06-28 06:30:00", "remind me to call mom")
        testExtract("remind me to call mom at 06 30 hours",
                    "2017-06-28 06:30:00", "remind me to call mom")
        testExtract("remind me to call mom at 06 30",
                    "2017-06-28 06:30:00", "remind me to call mom")
        testExtract("remind me to call mom at 06 30 hours",
                    "2017-06-28 06:30:00", "remind me to call mom")
        testExtract("remind me to call mom at 7 o'clock",
                    "2017-06-27 19:00:00", "remind me to call mom")
        testExtract("remind me to call mom this evening at 7 o'clock",
                    "2017-06-27 19:00:00", "remind me to call mom")
        testExtract("remind me to call mom  at 7 o'clock tonight",
                    "2017-06-27 19:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 7 o'clock in the morning",
                    "2017-06-28 07:00:00", "remind me to call mom")
        testExtract("remind me to call mom Thursday evening at 7 o'clock",
                    "2017-06-29 19:00:00", "remind me to call mom")
        testExtract("remind me to call mom Thursday morning at 7 o'clock",
                    "2017-06-29 07:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 7 o'clock Thursday morning",
                    "2017-06-29 07:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 7:00 Thursday morning",
                    "2017-06-29 07:00:00", "remind me to call mom")
        # TODO: This test is imperfect due to the "at 7:00" still in the
        #       remainder.  But let it pass for now since time is correct
        testExtract("remind me to call mom at 7:00 Thursday evening",
                    "2017-06-29 19:00:00", "remind me to call mom at 7:00")
        testExtract("remind me to call mom at 8 Wednesday evening",
                    "2017-06-28 20:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 8 Wednesday in the evening",
                    "2017-06-28 20:00:00", "remind me to call mom")
        testExtract("remind me to call mom Wednesday evening at 8",
                    "2017-06-28 20:00:00", "remind me to call mom")
        testExtract("remind me to call mom in two hours",
                    "2017-06-27 15:04:00", "remind me to call mom")
        testExtract("remind me to call mom in 2 hours",
                    "2017-06-27 15:04:00", "remind me to call mom")
        testExtract("remind me to call mom in 15 minutes",
                    "2017-06-27 13:19:00", "remind me to call mom")
        testExtract("remind me to call mom in fifteen minutes",
                    "2017-06-27 13:19:00", "remind me to call mom")
        testExtract("remind me to call mom at 10am 2 days after this saturday",
                    "2017-07-03 10:00:00", "remind me to call mom")
        testExtract("Play Rick Astley music 2 days from Friday",
                    "2017-07-02 00:00:00", "play rick astley music")
        testExtract("Begin the invasion at 3:45 pm on Thursday",
                    "2017-06-29 15:45:00", "begin invasion")
        testExtract("On Monday, order pie from the bakery",
                    "2017-07-03 00:00:00", "order pie from bakery")
        testExtract("Play Happy Birthday music 5 years from today",
                    "2022-06-27 00:00:00", "play happy birthday music")
        testExtract("Skype Mom at 12:45 pm next Thursday",
                    "2017-07-06 12:45:00", "skype mom")
        testExtract("What's the weather next Friday?",
                    "2017-06-30 00:00:00", "what weather")
        testExtract("What's the weather next Wednesday?",
                    "2017-07-05 00:00:00", "what weather")
        testExtract("What's the weather next Thursday?",
                    "2017-07-06 00:00:00", "what weather")
        testExtract("what is the weather next friday morning",
                    "2017-06-30 08:00:00", "what is weather")
        testExtract("what is the weather next friday evening",
                    "2017-06-30 19:00:00", "what is weather")
        testExtract("what is the weather next friday afternoon",
                    "2017-06-30 15:00:00", "what is weather")
        testExtract("remind me to call mom on august 3rd",
                    "2017-08-03 00:00:00", "remind me to call mom")
        testExtract("Buy fireworks on the 4th of July",
                    "2017-07-04 00:00:00", "buy fireworks")
        testExtract("what is the weather 2 weeks from next friday",
                    "2017-07-14 00:00:00", "what is weather")
        testExtract("what is the weather wednesday at 0700 hours",
                    "2017-06-28 07:00:00", "what is weather")
        testExtract("set an alarm wednesday at 7 o'clock",
                    "2017-06-28 07:00:00", "set alarm")
        testExtract("Set up an appointment at 12:45 pm next Thursday",
                    "2017-07-06 12:45:00", "set up appointment")
        testExtract("What's the weather this Thursday?",
                    "2017-06-29 00:00:00", "what weather")
        testExtract("set up the visit for 2 weeks and 6 days from Saturday",
                    "2017-07-21 00:00:00", "set up visit")
        testExtract("Begin the invasion at 03 45 on Thursday",
                    "2017-06-29 03:45:00", "begin invasion")
        testExtract("Begin the invasion at o 800 hours on Thursday",
                    "2017-06-29 08:00:00", "begin invasion")
        testExtract("Begin the party at 8 o'clock in the evening on Thursday",
                    "2017-06-29 20:00:00", "begin party")
        testExtract("Begin the invasion at 8 in the evening on Thursday",
                    "2017-06-29 20:00:00", "begin invasion")
        testExtract("Begin the invasion on Thursday at noon",
                    "2017-06-29 12:00:00", "begin invasion")
        testExtract("Begin the invasion on Thursday at midnight",
                    "2017-06-29 00:00:00", "begin invasion")
        testExtract("Begin the invasion on Thursday at 0500",
                    "2017-06-29 05:00:00", "begin invasion")
        testExtract("remind me to wake up in 4 years",
                    "2021-06-27 00:00:00", "remind me to wake up")
        testExtract("remind me to wake up in 4 years and 4 days",
                    "2021-07-01 00:00:00", "remind me to wake up")
        testExtract("What is the weather 3 days after tomorrow?",
                    "2017-07-01 00:00:00", "what is weather")
        testExtract("december 3",
                    "2017-12-03 00:00:00", "")
        testExtract("lets meet at 8:00 tonight",
                    "2017-06-27 20:00:00", "lets meet")
        testExtract("lets meet at 5pm",
                    "2017-06-27 17:00:00", "lets meet")
        testExtract("lets meet at 8 a.m.",
                    "2017-06-28 08:00:00", "lets meet")
        testExtract("remind me to wake up at 8 a.m",
                    "2017-06-28 08:00:00", "remind me to wake up")
        testExtract("what is the weather on tuesday",
                    "2017-06-27 00:00:00", "what is weather")
        testExtract("what is the weather on monday",
                    "2017-07-03 00:00:00", "what is weather")
        testExtract("what is the weather this wednesday",
                    "2017-06-28 00:00:00", "what is weather")
        testExtract("on thursday what is the weather",
                    "2017-06-29 00:00:00", "what is weather")
        testExtract("on this thursday what is the weather",
                    "2017-06-29 00:00:00", "what is weather")
        testExtract("on last monday what was the weather",
                    "2017-06-26 00:00:00", "what was weather")
        testExtract("set an alarm for wednesday evening at 8",
                    "2017-06-28 20:00:00", "set alarm")
        testExtract("set an alarm for wednesday at 3 o'clock in the afternoon",
                    "2017-06-28 15:00:00", "set alarm")
        testExtract("set an alarm for wednesday at 3 o'clock in the morning",
                    "2017-06-28 03:00:00", "set alarm")
        testExtract("set an alarm for wednesday morning at 7 o'clock",
                    "2017-06-28 07:00:00", "set alarm")
        testExtract("set an alarm for today at 7 o'clock",
                    "2017-06-27 19:00:00", "set alarm")
        testExtract("set an alarm for this evening at 7 o'clock",
                    "2017-06-27 19:00:00", "set alarm")
        # TODO: This test is imperfect due to the "at 7:00" still in the
        #       remainder.  But let it pass for now since time is correct
        testExtract("set an alarm for this evening at 7:00",
                    "2017-06-27 19:00:00", "set alarm at 7:00")
        testExtract("on the evening of june 5th 2017 remind me to" +
                    " call my mother",
                    "2017-06-05 19:00:00", "remind me to call my mother")
        # TODO: This test is imperfect due to the missing "for" in the
        #       remainder.  But let it pass for now since time is correct
        testExtract("update my calendar for a morning meeting with julius" +
                    " on march 4th",
                    "2018-03-04 08:00:00",
                    "update my calendar meeting with julius")
        testExtract("remind me to call mom next tuesday",
                    "2017-07-04 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom in 3 weeks",
                    "2017-07-18 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom in 8 weeks",
                    "2017-08-22 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom in 8 weeks and 2 days",
                    "2017-08-24 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom in 4 days",
                    "2017-07-01 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom in 3 months",
                    "2017-09-27 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom in 2 years and 2 days",
                    "2019-06-29 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom next week",
                    "2017-07-04 00:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 10am on saturday",
                    "2017-07-01 10:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 10am this saturday",
                    "2017-07-01 10:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 10 next saturday",
                    "2017-07-01 10:00:00", "remind me to call mom")
        testExtract("remind me to call mom at 10am next saturday",
                    "2017-07-01 10:00:00", "remind me to call mom")
        # test yesterday
        testExtract("what day was yesterday",
                    "2017-06-26 00:00:00", "what day was")
        testExtract("what day was the day before yesterday",
                    "2017-06-25 00:00:00", "what day was")
        testExtract("i had dinner yesterday at 6",
                    "2017-06-26 06:00:00", "i had dinner")
        testExtract("i had dinner yesterday at 6 am",
                    "2017-06-26 06:00:00", "i had dinner")
        testExtract("i had dinner yesterday at 6 pm",
                    "2017-06-26 18:00:00", "i had dinner")

        # Below two tests, ensure that time is picked
        # even if no am/pm is specified
        # in case of weekdays/tonight
        testExtract("set alarm for 9 on weekdays",
                    "2017-06-27 21:00:00", "set alarm weekdays")
        testExtract("for 8 tonight",
                    "2017-06-27 20:00:00", "")
        testExtract("for 8:30pm tonight",
                    "2017-06-27 20:30:00", "")
        # Tests a time with ':' & without am/pm
        testExtract("set an alarm for tonight 9:30",
                    "2017-06-27 21:30:00", "set alarm")
        testExtract("set an alarm at 9:00 for tonight",
                    "2017-06-27 21:00:00", "set alarm")
        # Check if it picks the intent irrespective of correctness
        testExtract("set an alarm at 9 o'clock for tonight",
                    "2017-06-27 21:00:00", "set alarm")
        testExtract("remind me about the game tonight at 11:30",
                    "2017-06-27 23:30:00", "remind me about game")
        testExtract("set alarm at 7:30 on weekdays",
                    "2017-06-27 19:30:00", "set alarm on weekdays")

        #  "# days <from X/after X>"
        testExtract("my birthday is 2 days from today",
                    "2017-06-29 00:00:00", "my birthday is")
        testExtract("my birthday is 2 days after today",
                    "2017-06-29 00:00:00", "my birthday is")
        testExtract("my birthday is 2 days from tomorrow",
                    "2017-06-30 00:00:00", "my birthday is")
        testExtract("my birthday is 2 days after tomorrow",
                    "2017-06-30 00:00:00", "my birthday is")
        testExtract("remind me to call mom at 10am 2 days after next saturday",
                    "2017-07-10 10:00:00", "remind me to call mom")
        testExtract("my birthday is 2 days from yesterday",
                    "2017-06-28 00:00:00", "my birthday is")
        testExtract("my birthday is 2 days after yesterday",
                    "2017-06-28 00:00:00", "my birthday is")

        #  "# days ago>"
        testExtract("my birthday was 1 day ago",
                    "2017-06-26 00:00:00", "my birthday was")
        testExtract("my birthday was 2 days ago",
                    "2017-06-25 00:00:00", "my birthday was")
        testExtract("my birthday was 3 days ago",
                    "2017-06-24 00:00:00", "my birthday was")
        testExtract("my birthday was 4 days ago",
                    "2017-06-23 00:00:00", "my birthday was")
        # TODO this test is imperfect due to "tonight" in the reminder, but let is pass since the date is correct
        testExtract("lets meet tonight",
                    "2017-06-27 22:00:00", "lets meet tonight")
        # TODO this test is imperfect due to "at night" in the reminder, but let is pass since the date is correct
        testExtract("lets meet later at night",
                    "2017-06-27 22:00:00", "lets meet later at night")
        # TODO this test is imperfect due to "night" in the reminder, but let is pass since the date is correct
        testExtract("what's the weather like tomorrow night",
                    "2017-06-28 22:00:00", "what is weather like night")
        # TODO this test is imperfect due to "night" in the reminder, but let is pass since the date is correct
        testExtract("what's the weather like next tuesday night",
                    "2017-07-04 22:00:00", "what is weather like night")

    def test_extract_ambiguous_time_en(self):
        morning = datetime(2017, 6, 27, 8, 1, 2, tzinfo=default_timezone())
        evening = datetime(2017, 6, 27, 20, 1, 2, tzinfo=default_timezone())
        noonish = datetime(2017, 6, 27, 12, 1, 2, tzinfo=default_timezone())
        self.assertEqual(
            extract_datetime('feed the fish'), None)
        self.assertEqual(
            extract_datetime('day'), None)
        self.assertEqual(
            extract_datetime('week'), None)
        self.assertEqual(
            extract_datetime('month'), None)
        self.assertEqual(
            extract_datetime('year'), None)
        self.assertEqual(
            extract_datetime(' '), None)
        self.assertEqual(
            extract_datetime('feed fish at 10 o\'clock', morning)[0],
            datetime(2017, 6, 27, 10, 0, 0, tzinfo=default_timezone()))
        self.assertEqual(
            extract_datetime('feed fish at 10 o\'clock', noonish)[0],
            datetime(2017, 6, 27, 22, 0, 0, tzinfo=default_timezone()))
        self.assertEqual(
            extract_datetime('feed fish at 10 o\'clock', evening)[0],
            datetime(2017, 6, 27, 22, 0, 0, tzinfo=default_timezone()))

    def test_extract_date_with_may_I_en(self):
        now = datetime(2019, 7, 4, 8, 1, 2, tzinfo=default_timezone())
        may_date = datetime(2019, 5, 2, 10, 11, 20, tzinfo=default_timezone())
        self.assertEqual(
            extract_datetime('May I know what time it is tomorrow', now)[0],
            datetime(2019, 7, 5, 0, 0, 0, tzinfo=default_timezone()))
        self.assertEqual(
            extract_datetime('May I when 10 o\'clock is', now)[0],
            datetime(2019, 7, 4, 10, 0, 0, tzinfo=default_timezone()))
        self.assertEqual(
            extract_datetime('On 24th of may I want a reminder', may_date)[0],
            datetime(2019, 5, 24, 0, 0, 0, tzinfo=default_timezone()))

    def test_extract_relativedatetime_en(self):
        def extractWithFormat(text):
            date = datetime(2017, 6, 27, 10, 1, 2, tzinfo=default_timezone())
            [extractedDate, leftover] = extract_datetime(text, date)
            extractedDate = extractedDate.strftime("%Y-%m-%d %H:%M:%S")
            return [extractedDate, leftover]

        def testExtract(text, expected_date, expected_leftover):
            res = extractWithFormat(normalize(text))
            self.assertEqual(res[0], expected_date, "for=" + text)
            self.assertEqual(res[1], expected_leftover, "for=" + text)

        testExtract("lets meet in 5 minutes",
                    "2017-06-27 10:06:02", "lets meet")
        testExtract("lets meet in 5minutes",
                    "2017-06-27 10:06:02", "lets meet")
        testExtract("lets meet in 5 seconds",
                    "2017-06-27 10:01:07", "lets meet")
        testExtract("lets meet in 1 hour",
                    "2017-06-27 11:01:02", "lets meet")
        testExtract("lets meet in 2 hours",
                    "2017-06-27 12:01:02", "lets meet")
        testExtract("lets meet in 2hours",
                    "2017-06-27 12:01:02", "lets meet")
        testExtract("lets meet in 1 minute",
                    "2017-06-27 10:02:02", "lets meet")
        testExtract("lets meet in 1 second",
                    "2017-06-27 10:01:03", "lets meet")
        testExtract("lets meet in 5seconds",
                    "2017-06-27 10:01:07", "lets meet")

    def test_normalize_numbers(self):
        self.assertEqual(normalize("remind me to do something at two to two"),
                         "remind me to do something at 2 to 2")
        self.assertEqual(normalize('what time will it be in two minutes'),
                         'what time will it be in 2 minutes')
        self.assertEqual(
            normalize('What time will it be in twenty two minutes'),
            'What time will it be in 22 minutes')
        self.assertEqual(
            normalize("remind me to do something at twenty to two"),
            "remind me to do something at 20 to 2")

        # TODO imperfect test, maybe should return 'my favorite numbers are 20 2',
        #  let is pass for now since this is likely a STT issue if ever
        #  encountered in the wild and is somewhat ambiguous, if this was
        #  spoken by a human the result is what we expect, if in written form
        #  it is ambiguous but could mean separate numbers
        self.assertEqual(normalize('my favorite numbers are twenty 2'),
                         'my favorite numbers are 22')
        # TODO imperfect test, same as above, fixing would impact
        #  extract_numbers quite a bit and require a non trivial ammount of
        #  refactoring
        self.assertEqual(normalize('my favorite numbers are 20 2'),
                         'my favorite numbers are 22')

        # test ordinals
        self.assertEqual(normalize('this is the first'),
                         'this is first')
        self.assertEqual(normalize('this is the first second'),
                         'this is first second')
        self.assertEqual(normalize('this is the first second and third'),
                         'this is first second and third')

        # test fractions
        self.assertEqual(normalize('whole hour'),
                         'whole hour')
        self.assertEqual(normalize('quarter hour'),
                         'quarter hour')
        self.assertEqual(normalize('halve hour'),
                         'halve hour')
        self.assertEqual(normalize('half hour'),
                         'half hour')

    def test_extract_date_with_number_words(self):
        now = datetime(2019, 7, 4, 8, 1, 2, tzinfo=default_timezone())
        self.assertEqual(
            extract_datetime('What time will it be in 2 minutes', now)[0],
            datetime(2019, 7, 4, 8, 3, 2, tzinfo=default_timezone()))
        self.assertEqual(
            extract_datetime('What time will it be in two minutes', now)[0],
            datetime(2019, 7, 4, 8, 3, 2, tzinfo=default_timezone()))
        self.assertEqual(
            extract_datetime('What time will it be in two hundred minutes',
                             now)[0],
            datetime(2019, 7, 4, 11, 21, 2, tzinfo=default_timezone()))

    def test_spaces(self):
        self.assertEqual(normalize("  this   is  a    test"),
                         "this is test")
        self.assertEqual(normalize("  this   is  a    test  "),
                         "this is test")
        self.assertEqual(normalize("  this   is  one    test"),
                         "this is 1 test")

    def test_numbers(self):
        self.assertEqual(normalize("this is a one two three  test"),
                         "this is 1 2 3 test")
        self.assertEqual(normalize("  it's  a four five six  test"),
                         "it is 4 5 6 test")
        self.assertEqual(normalize("it's  a seven eight nine test"),
                         "it is 7 8 9 test")
        self.assertEqual(normalize("it's a seven eight nine  test"),
                         "it is 7 8 9 test")
        self.assertEqual(normalize("that's a ten eleven twelve test"),
                         "that is 10 11 12 test")
        self.assertEqual(normalize("that's a thirteen fourteen test"),
                         "that is 13 14 test")
        self.assertEqual(normalize("that's fifteen sixteen seventeen"),
                         "that is 15 16 17")
        self.assertEqual(normalize("that's eighteen nineteen twenty"),
                         "that is 18 19 20")
        self.assertEqual(normalize("that's one nineteen twenty two"),
                         "that is 1 19 22")
        self.assertEqual(normalize("that's one hundred"),
                         "that is 100")
        self.assertEqual(normalize("that's one two twenty two"),
                         "that is 1 2 22")
        self.assertEqual(normalize("that's one and a half"),
                         "that is 1 and half")
        self.assertEqual(normalize("that's one and a half and five six"),
                         "that is 1 and half and 5 6")

    def test_multiple_numbers(self):
        self.assertEqual(extract_numbers("this is a one two three  test"),
                         [1.0, 2.0, 3.0])
        self.assertEqual(extract_numbers("it's  a four five six  test"),
                         [4.0, 5.0, 6.0])
        self.assertEqual(extract_numbers("this is a ten eleven twelve  test"),
                         [10.0, 11.0, 12.0])
        self.assertEqual(extract_numbers("this is a one twenty one  test"),
                         [1.0, 21.0])
        self.assertEqual(extract_numbers("1 dog, seven pigs, macdonald had a "
                                         "farm, 3 times 5 macarena"),
                         [1, 7, 3, 5])
        self.assertEqual(extract_numbers("two beers for two bears"),
                         [2.0, 2.0])
        self.assertEqual(extract_numbers("twenty 20 twenty"),
                         [20, 20, 20])
        self.assertEqual(extract_numbers("twenty 20 22"),
                         [20.0, 20.0, 22.0])
        self.assertEqual(extract_numbers("twenty twenty two twenty"),
                         [20, 22, 20])
        self.assertEqual(extract_numbers("twenty 2"),
                         [22.0])
        self.assertEqual(extract_numbers("twenty 20 twenty 2"),
                         [20, 20, 22])
        self.assertEqual(extract_numbers("third one"),
                         [1 / 3, 1])
        self.assertEqual(extract_numbers("third one", ordinals=True), [3])
        self.assertEqual(extract_numbers("six trillion", short_scale=True),
                         [6e12])
        self.assertEqual(extract_numbers("six trillion", short_scale=False),
                         [6e18])
        self.assertEqual(extract_numbers("two pigs and six trillion bacteria",
                                         short_scale=True), [2, 6e12])
        self.assertEqual(extract_numbers("two pigs and six trillion bacteria",
                                         short_scale=False), [2, 6e18])
        self.assertEqual(extract_numbers("thirty second or first",
                                         ordinals=True), [32, 1])
        self.assertEqual(extract_numbers("this is a seven eight nine and a"
                                         " half test"),
                         [7.0, 8.0, 9.5])

    def test_contractions(self):
        self.assertEqual(normalize("ain't"), "is not")
        self.assertEqual(normalize("aren't"), "are not")
        self.assertEqual(normalize("can't"), "can not")
        self.assertEqual(normalize("could've"), "could have")
        self.assertEqual(normalize("couldn't"), "could not")
        self.assertEqual(normalize("didn't"), "did not")
        self.assertEqual(normalize("doesn't"), "does not")
        self.assertEqual(normalize("don't"), "do not")
        self.assertEqual(normalize("gonna"), "going to")
        self.assertEqual(normalize("gotta"), "got to")
        self.assertEqual(normalize("hadn't"), "had not")
        self.assertEqual(normalize("hadn't have"), "had not have")
        self.assertEqual(normalize("hasn't"), "has not")
        self.assertEqual(normalize("haven't"), "have not")
        # TODO: Ambiguous with "he had"
        self.assertEqual(normalize("he'd"), "he would")
        self.assertEqual(normalize("he'll"), "he will")
        # TODO: Ambiguous with "he has"
        self.assertEqual(normalize("he's"), "he is")
        # TODO: Ambiguous with "how would"
        self.assertEqual(normalize("how'd"), "how did")
        self.assertEqual(normalize("how'll"), "how will")
        # TODO: Ambiguous with "how has" and "how does"
        self.assertEqual(normalize("how's"), "how is")
        # TODO: Ambiguous with "I had"
        self.assertEqual(normalize("I'd"), "I would")
        self.assertEqual(normalize("I'll"), "I will")
        self.assertEqual(normalize("I'm"), "I am")
        self.assertEqual(normalize("I've"), "I have")
        self.assertEqual(normalize("I haven't"), "I have not")
        self.assertEqual(normalize("isn't"), "is not")
        self.assertEqual(normalize("it'd"), "it would")
        self.assertEqual(normalize("it'll"), "it will")
        # TODO: Ambiguous with "it has"
        self.assertEqual(normalize("it's"), "it is")
        self.assertEqual(normalize("it isn't"), "it is not")
        self.assertEqual(normalize("mightn't"), "might not")
        self.assertEqual(normalize("might've"), "might have")
        self.assertEqual(normalize("mustn't"), "must not")
        self.assertEqual(normalize("mustn't have"), "must not have")
        self.assertEqual(normalize("must've"), "must have")
        self.assertEqual(normalize("needn't"), "need not")
        self.assertEqual(normalize("oughtn't"), "ought not")
        self.assertEqual(normalize("shan't"), "shall not")
        # TODO: Ambiguous wiht "she had"
        self.assertEqual(normalize("she'd"), "she would")
        self.assertEqual(normalize("she hadn't"), "she had not")
        self.assertEqual(normalize("she'll"), "she will")
        self.assertEqual(normalize("she's"), "she is")
        self.assertEqual(normalize("she isn't"), "she is not")
        self.assertEqual(normalize("should've"), "should have")
        self.assertEqual(normalize("shouldn't"), "should not")
        self.assertEqual(normalize("shouldn't have"), "should not have")
        self.assertEqual(normalize("somebody's"), "somebody is")
        # TODO: Ambiguous with "someone had"
        self.assertEqual(normalize("someone'd"), "someone would")
        self.assertEqual(normalize("someone hadn't"), "someone had not")
        self.assertEqual(normalize("someone'll"), "someone will")
        # TODO: Ambiguous with "someone has"
        self.assertEqual(normalize("someone's"), "someone is")
        self.assertEqual(normalize("that'll"), "that will")
        # TODO: Ambiguous with "that has"
        self.assertEqual(normalize("that's"), "that is")
        # TODO: Ambiguous with "that had"
        self.assertEqual(normalize("that'd"), "that would")
        # TODO: Ambiguous with "there had"
        self.assertEqual(normalize("there'd"), "there would")
        self.assertEqual(normalize("there're"), "there are")
        # TODO: Ambiguous with "there has"
        self.assertEqual(normalize("there's"), "there is")
        # TODO: Ambiguous with "they had"
        self.assertEqual(normalize("they'd"), "they would")
        self.assertEqual(normalize("they'll"), "they will")
        self.assertEqual(normalize("they won't have"), "they will not have")
        self.assertEqual(normalize("they're"), "they are")
        self.assertEqual(normalize("they've"), "they have")
        self.assertEqual(normalize("they haven't"), "they have not")
        self.assertEqual(normalize("wasn't"), "was not")
        # TODO: Ambiguous wiht "we had"
        self.assertEqual(normalize("we'd"), "we would")
        self.assertEqual(normalize("we would've"), "we would have")
        self.assertEqual(normalize("we wouldn't"), "we would not")
        self.assertEqual(normalize("we wouldn't have"), "we would not have")
        self.assertEqual(normalize("we'll"), "we will")
        self.assertEqual(normalize("we won't have"), "we will not have")
        self.assertEqual(normalize("we're"), "we are")
        self.assertEqual(normalize("we've"), "we have")
        self.assertEqual(normalize("weren't"), "were not")
        self.assertEqual(normalize("what'd"), "what did")
        self.assertEqual(normalize("what'll"), "what will")
        self.assertEqual(normalize("what're"), "what are")
        # TODO: Ambiguous with "what has" / "what does")
        self.assertEqual(normalize("whats"), "what is")
        self.assertEqual(normalize("what's"), "what is")
        self.assertEqual(normalize("what've"), "what have")
        # TODO: Ambiguous with "when has"
        self.assertEqual(normalize("when's"), "when is")
        self.assertEqual(normalize("where'd"), "where did")
        # TODO: Ambiguous with "where has" / where does"
        self.assertEqual(normalize("where's"), "where is")
        self.assertEqual(normalize("where've"), "where have")
        # TODO: Ambiguous with "who had" "who did")
        self.assertEqual(normalize("who'd"), "who would")
        self.assertEqual(normalize("who'd've"), "who would have")
        self.assertEqual(normalize("who'll"), "who will")
        self.assertEqual(normalize("who're"), "who are")
        # TODO: Ambiguous with "who has" / "who does"
        self.assertEqual(normalize("who's"), "who is")
        self.assertEqual(normalize("who've"), "who have")
        self.assertEqual(normalize("why'd"), "why did")
        self.assertEqual(normalize("why're"), "why are")
        # TODO: Ambiguous with "why has" / "why does"
        self.assertEqual(normalize("why's"), "why is")
        self.assertEqual(normalize("won't"), "will not")
        self.assertEqual(normalize("won't've"), "will not have")
        self.assertEqual(normalize("would've"), "would have")
        self.assertEqual(normalize("wouldn't"), "would not")
        self.assertEqual(normalize("wouldn't've"), "would not have")
        self.assertEqual(normalize("ya'll"), "you all")
        self.assertEqual(normalize("y'all"), "you all")
        self.assertEqual(normalize("y'ain't"), "you are not")
        # TODO: Ambiguous with "you had"
        self.assertEqual(normalize("you'd"), "you would")
        self.assertEqual(normalize("you'd've"), "you would have")
        self.assertEqual(normalize("you'll"), "you will")
        self.assertEqual(normalize("you're"), "you are")
        self.assertEqual(normalize("you aren't"), "you are not")
        self.assertEqual(normalize("you've"), "you have")
        self.assertEqual(normalize("you haven't"), "you have not")

    def test_combinations(self):
        self.assertEqual(normalize("I couldn't have guessed there'd be two"),
                         "I could not have guessed there would be 2")
        self.assertEqual(normalize("I wouldn't have"), "I would not have")
        self.assertEqual(normalize("I hadn't been there"),
                         "I had not been there")
        self.assertEqual(normalize("I would've"), "I would have")
        self.assertEqual(normalize("it hadn't"), "it had not")
        self.assertEqual(normalize("it hadn't have"), "it had not have")
        self.assertEqual(normalize("it would've"), "it would have")
        self.assertEqual(normalize("she wouldn't have"), "she would not have")
        self.assertEqual(normalize("she would've"), "she would have")
        self.assertEqual(normalize("someone wouldn't have"),
                         "someone would not have")
        self.assertEqual(normalize("someone would've"), "someone would have")
        self.assertEqual(normalize("what's the weather like"),
                         "what is weather like")
        self.assertEqual(normalize("that's what I told you"),
                         "that is what I told you")

        self.assertEqual(normalize("whats 8 + 4"), "what is 8 + 4")

    # TODO not localized; needed in english?
    def test_gender(self):
        self.assertRaises((AttributeError, FunctionNotLocalizedError),
                          get_gender, "person", None)


class TestQuantulum(unittest.TestCase):
    def test_extract_units(self):
        self.assertEqual(extract_quantities("100 W"), [(100.0, '100 W')])
        # TODO quantulum 3 bug (doesnt always happen)
        # self.assertEqual(extract_quantities("I want 2 liters of wine"),
        #                 [(2.0, '2 liters')])
        self.assertEqual(extract_quantities("I want 10 beers"),
                         [(10.0, '10')])
        self.assertEqual(extract_quantities("The outside temperature is 35°F"),
                         [(35.0, '35°F')])
        self.assertEqual(extract_quantities('Sound travels at 0.34 km/s'),
                         [(0.34, '0.34 km/s')])
        self.assertEqual(extract_quantities(
            "The LHC smashes proton beams at 12.8–13.0 TeV"),
            [(12.9, '12.8–13.0 TeV')])
        self.assertEqual(
            extract_quantities("Gimme $1e10 now and also 1 TW and 0.5 J!"),
            [(10000000000.0, '$1e10'), (1.0, '1 TW'), (0.5, '0.5 J')])

        self.assertEqual(extract_quantities(
            "The LHC smashes proton beams at 12.8–13.0 TeV", raw=True),
            [{'span': (32, 45),
              'text': '12.8–13.0 TeV',
              'uncertainty': 0.09999999999999964,
              'unit': 'teraelectron volt',
              'value': 12.9}]
        )


class TestNER(unittest.TestCase):
    def test_extract_entities(self):
        self.assertEqual(extract_entities("I want 2 liters of wine"),
                         [{'confidence': 1,
                           'entity_type': EntityType.QUANTITY,
                           'span': (7, 15),
                           'value': '2 liters'},
                          {'confidence': 0.5,
                           'entity_type': EntityType.KEYWORD,
                           'span': (19, 23),
                           'value': 'wine'}
                          ])

        self.assertEqual(extract_entities("How is the weather in London"),
                         [{'confidence': 0.5,
                           'entity_type': EntityType.KEYWORD,
                           'span': (11, 18),
                           'value': 'weather'},
                          {'confidence': 0.9,
                           'entity_type': EntityType.LOCATION,
                           'span': (22, 28),
                           'value': 'London'}
                          ])

        self.assertEqual(extract_entities("Mark Zuckerberg is not human"),
                         [{'confidence': 0.8,
                           'entity_type': EntityType.ENTITY,
                           'span': (0, 15),
                           'value': 'Mark Zuckerberg'}
                          ])

    def test_extract_raw(self):
        self.assertEqual(
            extract_entities("London and Lisbon are capital cities",
                             raw=True),
            [{'confidence': 0.9,
              'data': {'country_code': 'GB',
                       'country_name': 'United Kingdom',
                       'hemisphere': 'north',
                       'latitude': 54,
                       'longitude': -2,
                       'name': 'London'},
              'entity_type': EntityType.LOCATION,
              'rules': [],
              'source_text': 'London and Lisbon are capital cities',
              'spans': [(0, 6)],
              'value': 'London'},
             {'confidence': 0.9,
              'data': {'country_code': 'PT',
                       'country_name': 'Portugal',
                       'hemisphere': 'north',
                       'latitude': 39.5,
                       'longitude': -8,
                       'name': 'Lisbon'},
              'entity_type': EntityType.LOCATION,
              'rules': [],
              'source_text': 'London and Lisbon are capital cities',
              'spans': [(11, 17)],
              'value': 'Lisbon'},
             {'confidence': 0.6666666666666666,
              'data': {'score': 4.0},
              'entity_type': EntityType.KEYWORD,
              'rules': [],
              'source_text': 'London and Lisbon are capital cities',
              'spans': [(22, 36)],
              'value': 'capital cities'}]
        )

    def test_extract_query(self):
        self.assertEqual(extract_query("Who is Mark Zuckerberg"),
                         "Mark Zuckerberg")

        self.assertEqual(extract_query("buy 2 liters of wine"),
                         "2 liters wine")
        self.assertEqual(extract_query("buy 2 liters of wine",
                                       best_entity=True),
                         "2 liters")

        self.assertEqual(extract_query("How is the weather in London"),
                         "weather London")
        self.assertEqual(extract_query("How is the weather in London",
                                       best_entity=True),
                         "London")

        self.assertEqual(extract_query("what is the speed of light"),
                         "speed light")
        self.assertEqual(extract_query("what is the speed of light",
                                       best_entity=True),
                         "speed")
        self.assertEqual(extract_query("what is the speed of darkness"),
                         "speed darkness")
        self.assertEqual(extract_query("what is the speed of darkness",
                                       best_entity=True),
                         "darkness")

        self.assertEqual(extract_query("When is Isaac Newton birthday"),
                         "Isaac Newton birthday")
        self.assertEqual(extract_query("When is Isaac Newton birthday",
                                       best_entity=True),
                         "Isaac Newton")


class TestAbbreviationQuestions(unittest.TestCase):
    def test_abbr(self):
        test = [
            "What 's the abbreviation for limited partnership ?",
            "What 's the abbreviation for trinitrotoluene ?",
            "What does the number `` 5 '' stand for on FUBU clothing ?",
            #   "What is Mikhail Gorbachev 's middle initial ?",
            "What is the abbreviated expression for the National Bureau of Investigation ?",
            "What is the abbreviated form of the National Bureau of Investigation ?",
            "What is the abbreviated term used for the National Bureau of Investigation ?",
            "What is the abbreviation for Original Equipment Manufacturer ?",
            "What is the abbreviation for Texas ?",
            "What is the abbreviation for micro ?",
            "What is the abbreviation of General Motors ?",
            "What is the abbreviation of the International Olympic Committee ?",
            "What is the abbreviation of the National Bureau of Investigation ?",
            "What is the abbreviation of the company name ` General Motors ' ?",
            "What is the acronym for the National Bureau of Investigation ?",
            "What is the acronym for the rating system for air conditioner efficiency ?",
            "What is the correct way to abbreviate cc. at the bottom of a business letter ?",
        ]
        for q in test:
            self.assertIn(QuestionSubType.ABBREVIATION,
                          predict_question_type(q))

    def test_abbr_explain(self):
        lower = [
            "What is p.m. an abbreviation for , as in 5 p.m. ?",
            #  "What is the full form of .com ?",
            "What does e.g. stand for ?",
            "What does pH stand for ?",
            "What does snafu stand for ?",

            "What does the abbreviation cwt. mean ?",
            "What does the `` c '' stand for in the equation E=mc2 ?",
        ]
        test = [
            "What is the full name of the PLO ?",
            "CNN is an acronym for what ?",
            "CNN is the abbreviation for what ?",
            "CPR is the abbreviation for what ?",
            "In a computer , what does SCSI mean ?",
            "What do the letters CE stand for on so many products , particularly electrical , purchased now ?",
            "What do the letters D.C. stand for in Washington , D.C. ?",
            "What do the letters ZIP stand for in the phrase `` ZIP code '' ?",
            "What does A&W of root beer fame stand for ?",
            "What does BMW stand for ?",
            "What does BTU mean ?",
            "What does BUD stand for ?",
            "What does CNN stand for ?",
            "What does CPR stand for ?",
            "What does EKG stand for ?",
            "What does G.M.T. stand for ?",
            "What does HIV stand for ?",
            "What does I.V. stand for ?",
            "What does IBM stand for ?",
            "What does INRI stand for when used on Jesus ' cross ?",
            "What does IOC stand for ?",
            "What does IQ stand for ?",
            "What does JESSICA mean ?",
            "What does LOL mean ?",
            "What does MSG stand for ?",
            "What does Ms. , Miss , and Mrs. stand for ?",
            "What does NAFTA stand for ?",
            "What does NASA stand for ?",
            "What does NASDAQ stand for ?",
            "What does NECROSIS mean ?",
            "What does R.E.M. stand for , as in the rock group R.E.M. ?",
            "What does RCA stand for ?",
            "What does S.O.S. stand for ?",
            "What does SHIELD stand for ?",
            "What does SIDS stand for ?",
            "What does U.S.S.R. stand for ?",
            "What does USPS stand for ?",
            "What does VCR stand for ?",
            "What does PSI stand for ?",
            "What does B.Y.O.B. mean ?",
            "What does the E stand for in the equation E=mc2 ?",
            "What does the T.S. stand for in T.S. Eliot 's name ?",
            "What does the abbreviation AIDS stand for ?",
            "What does the abbreviation IOC stand for ?",
            "What does the abbreviation OAS stand for ?",
            "What does the abbreviation SOS mean ?",
            "What does the acronym CPR mean ?",
            "What does the acronym NASA stand for ?",
            "What does the channel ESPN stand for ?",
            "What does the technical term ISDN mean ?",
            "What does the word LASER mean ?",
            "What is AFS ?",
            "What is BPH ?",
            "What is DEET ?",
            "What is DSL ?",
            "What is DTMF ?",
            "What is HDLC ?",
            "What is HTML ?",
            "What is IOC an abbreviation of ?",
            "What is LMDS ?",
            "What is RAM in the computer ?",
            "What is RCD ?",
            "What is SAP ?",
            "What is SVHS ?",
            "What is TMJ ?",
            "What is a USB port on a computer ?",
            "When reading classified ads , what does EENTY : other stand for ?",
        ]
        for q in lower + test:
            self.assertIn(QuestionSubType.ABBREVIATION_EXPLANATION,
                          predict_question_type(q))


class TestHumanQuestions(unittest.TestCase):
    def test_individual(self):
        test = [
            "Who was the 22nd President of the US ?",
            "CNN is owned by whom ?",
            #   "In Dana 's `` Two Years Before the Mast , '' what seafarers lived
            #   in an abandoned oven on the beach at San Diego ?",
            "In the movie Groundshog Day what is the name of the character played by Andie MacDowell ?",
            "In the past 8 years who have the MVP players for the NHL been ?",
            "Name 11 famous martyrs .",
            "Name Alvin 's brothers",
            "Name Dick Tracy 's two children .",
            "Name Dondi 's adoptive grandfather .",
            "Name Randy Craft 's lawyer .",
            "Name a canine cartoon character other than Huckleberry Hound to have a voice by Daws Butler .",
            "Name a female figure skater .",
            "Name of heroine in `` Scruples '' ?",
            "Name of scholar on whose literal translations from the Chinese and Japanese Ezra Pound depended ?",
            "Name of the lady the Great Gatsby pines for ?",
            "Name of the powerful white trader in Conrad 's `` Heart of Darkness '' ?",
            "Name one of King Henry VIII 's wives .",
            "Name one of the major gods of Hinduism .",
            "Name the Four Horsemen of the Apocalypse .",
            "Name the On Stage character whose face was never seen .",
            "Name the Ranger who was always after Yogi Bear .",
            "Name the U.S. Senate majority leader and the Speaker of the House .",
            "Name the blind sculptress in love with the Fantastic Four 's Thing .",
            "Name the cartoon genie conjured by the magic ring shared by Nancy and Chuck .",
            "Name the child left on a doorstep at the beginning of Gasoline Alley .",
            "Name the creator of `` The Muppets '' .",
            "Name the designer of the shoe that spawned millions of plastic imitations , known as ` jellies ' .",
            "Name the first Russian astronaut to do a spacewalk .",
            "Name the first private citizen to fly in space .",
            "Name the lawyer for Randy Craft .",
            "Name the person who burst through the screen in the Lite beer commercials .",
            "Name the poet of the poem which begins : I do not know much about gods ; but I think that the river Is a strong brown god-sullen , and untamed ?",
            "Name the scar-faced bounty hunter of The Old West .",
            "Name the two actress daughters of John Mills .",
            "Name the two blob members of the animated Herculoids .",
            "Name the two youngsters saved by the animated Moby Dick .",
            "Name the various costumed personas of Dr. Henry Pym .",
            "President Bush compared Saddam Hussein to whom ?",
            "Rotary engines used to be made by whom ?",
            "Saddam Hussein was compared to whom by President Bush ?",
            "Silly putty was invented by whom ?",
            "The lawyer who represented Randy Craft , what was his name ?",
            "The name of the actor who played the detective in the film Kindergarden Cop is what ?",
            "What 's comic strip photographer Peter Parker 's secret identity ?",
            "What 's the better-known identity of John Merrick , the noble ogre of Victorian England ?",
            "What 's the middle name of movie producer Joseph E. Levine ?",
            "What 's the most common name in nursery rhymes ?",
            "What 's the most common surname in America ?",
            "What 's the name of Popeye 's adopted son ?",
            "What 's the name of Tom Sawyer 's aunt with whom he lives ?",
            "What 's the name of the actress who starred in the movie , `` Silence of the Lambs '' ?",
            "What 's the name of the star of the cooking show , `` Galloping Gourmet '' ?",
            "What 's the nickname of oddsmaker Jimmy Snyder ?",
            #  "What 1920s cowboy star rode Tony the Wonder Horse ?",
            "What 19th-century painter died in the Marquesas Islands ?",
            #   "What 19th-century writer had a country estate on the Hudson dubbed Sunnyside ?",
            #  "What 2th-century American poet wrote a four-volume biography of
            #  Abraham Lincoln ?",
            #  "What 2th-century fictional character attends Pencey Prep School ?",
            "What 4-foot-9 actress in 1984 became the first performer to win an Oscar for playing a character of the opposite sex ?",
            "What American actress was the first to be called a `` vamp '' ?",
            #   "What American composer wrote the music for `` West Side Story '' ?",
            #  "What American naval officer broke Japan 's isolationist policy in
            #  1853 ?",
            #    "What American poet wrote : `` Good fences make good neighbors '' ?",
            #  "What American sergeant lost both of his hands in combat during
            #  World War II and then went on to act in a single movie for which he won two Oscars ?",
            #  "What American won the world Grand Prix driving championship in
            #  1978 ?",
            #    "What Apollo 11 astronaut minded the store while Armstrong and
            #    Aldrin made history ?",
            #    "What Argentine boxer was shot dead outside a Nevada brothel in May ?",
            #    "What Argentine revolutionary fought with Castro and died in
            #    Bolivia in May , 1979 ?",
            "What Asian leader was known as The Little Brown Saint ?",
            "What Asian spiritual and political leader was married at the age of 13 ?",
            "What Batman character tools around on a Batcycle ?",
            #   "What British commander surrendered to George Washington at
            #   Yorktown in 1781 ?",
            #   "What British female pop singing star of the 1960s and early 1970s
            #   was a child actress in the 1940s and '50s ?",
            #   "What British general surrendered to the colonial army at Saratoga ?",
            #    "What British monarch 's lap did P.T. Barnum 's Tom Thumb sit in ?",
            #    "What British prime minister and U.S. president were seventh
            #    cousins once-removed ?",
            #    "What California governor said : `` Inaction may be the highest
            #    form of action '' ?",
            "What Catch-22 character is elected mayor of half a dozen Italian cities ?",
            #  "What Cherokee Indian gave his name to a tree ?",
            "What Chilean president was killed in a 1973 coup d 'etat ?",
            #    "What Civil War general wreaked havoc on the south by marching
            #    through Georgia on his way to the sea ?",
            #   "What Democratic prankster waved the train out of the station while Richard Nixon spoke from the caboose ?",
            #  "What Dynasty star made her 2th Century-Fox debut in The Virgin
            #  Queen ?",
            # "What English explorer discovered and named Virginia ?",
            # "What English physician was born on January 18 , 1779 and went on
            # to create two important inventions ?",
            # "What English playwright penned : `` Where the bee sucks , so shall I '' ?",
            "What English queen had seventeen children ?",
            "What English queen had six fingers on one hand ?",
            #   "What French designer declared : `` The jean is the destructor ! It is a dictator ! It is destroying creativity. The jean must be stopped ! '' ?",
            "What French leader sold Louisiana to the United States ?",
            "What French ruler was defeated at the battle of Waterloo ?",
            #  "What Frenchman claimed the following ? If God did not exist ,
            #  it would be necessary to invent him . ''",
            #  "What Good Little Witch is Casper 's girlfriend ?",
            #  "What Green Bay Packers coach philosophized : `` There 's nothing
            #  that stokes the fire like hate '' ?",
            #  "What Hall of Fame pitcher started three World Series Games for the New York Yankees in 1962 ?",
            "What Honeymooners actress did Television magazine name as 1953 's most promising star ?",
            #  "What Hungarian cardinal was first a state prisoner and then a
            #  refugee in the U.S. embassy 1956-1971 ?",
            "What Italian leader had a lifelong fear of the evil eye ?",
            "What Louisiana Senator won a seat that had been held by his father and mother ?",
            "What Mexican leader was shot dead in 1923 ?",
            "What Mormon leader was said to have had 27 wives ?",
            #  "What National Basketball Association superstar told his story in
            #  Giant Steps ?",
            "What Nazi leader killed himself in jail just before he was to be executed as a war criminal ?",
            #  "What New Orleans D.A. claimed : `` My staff and I solved the
            #  assassination weeks ago '' ?",
            #  "What New York Yankee was known as The Iron Horse ?",
            #  "What Nobel laureate was expelled from the Philippines before the
            #  conference on East Timor ?",
            #   "What Pope inaugurated Vatican International Radio ?",
            "What President 's favorite Biblical quotation was : `` Come now , and let us reason together '' .",
            "What President became Chief Justice after his presidency ?",
            "What President dispatched a cruiser to carry Charles Lindbergh home after his epic flight ?",
            "What President had never held an elected office until he was elected to the White House ?",
            "What President hit the jogging paths to enhance his athletic image and , sporting No. 39 , almost collapsed during the road race ?",
            "What President lived at 219 North Delaware Street , Independence , Missouri ?",
            "What President once told Gene Autry : `` Please give my regards to your wife Dale '' ?",
            "What President served for five years , six months and 2 days ?",
            "What President was assassinated by Charles J. Guiteau ?",
            "What President was buried at his ancestral home overlooking the Hudson River at Hyde Park , New York ?",
            "What President was meant for , but never placed in , the empty crypt beneath the capital 's rotunda ?",
            #  "What President-to-be was the first member of Congress to enlist
            #  following the attack on Pearl Harbor ?",
            #  "What Pulitzer Prize-winning novelist ran for mayor of New York
            #  City ?",
            #  "What Russian composer 's Prelude in C Sharp Minor brought him fame and fortune ?",
            #  "What Russian master spy lived in the U.S. under the name Emil
            #  Goldfus ?",
            #  "What Scottish poet penned To a Mouse and To a Louse ?",
            "What South Vietnamese president was assassinated by his generals in 1963 ?",
            "What Soviet leader owned a Rolls-Royce ?",
            "What Spanish artist painted Crucifixion ?",
            "What TV character said ; `` One of these days , Alice , pow , right in the kisser '' ?",
            "What TV character sired a horse named Thunder ?",
            #   "What TV comedian worked with White Fang , Black Tooth and Pookie
            #   the Lion ?",
            #   "What TV comediennes 's characters include former movie star Nora
            #   Desmond , secretary Mrs. Wiggins and a housewife named Eunice ?",
            #   "What TV detective did Craig Stevens play ?",
            #   "What TV family sometimes buys eclairs from Nelson 's Bakery ?",
            "What TV sitcom character had the maiden name Ethel Potter ?",
            #   "What TV talk-show host lends his name to a line of men 's clothing ?",
            #   "What Texas surgeon performed the first artificial heart transplant ?",
            #   "What U.S. Air Force general led the first bombing raid over Tokyo ?",
            #   "What U.S. Congressman said : `` Keep the faith , baby '' .",
            "What U.S. President had brothers-in-law in the Confederate army ?",
            "What U.S. President showed a fondness for munching on bee pollen bars ?",
            "What U.S. President was the first to breed mules ?",
            #  "What U.S. general died December 1 , 1945 , when his jeep collided
            #  with a truck ?",
            #  "What U.S. general was court-martialled for criticizing American
            #  air power ?",
            "What U.S. senator once played basketball for the New York Knicks ?",
            "What U.S. vice-president killed Alexander Hamilton in a duel ?",
            "What U.S. vice-president once declared : `` If you 've seen one slum , you 've seen them all '' ?",
            "What U.S. vice-president said : `` Some newspapers dispose of their garbage by printing it '' ?",
            "What United States President had dreamed that he was assassinated ?",
            "What World War II leader declared : `` The blow has been struck '' ?",
            #  "What `` marvelous '' major-league baseball player is now a
            #  spokesman for a beer company ?",
            "What actor 's autobiography is titled All My Yesterdays ?",
            "What actor , who had greatest fame on TV , became the father of triplets ?",
            "What actor and World War II airman had a $5 , 0 bounty put on his head by Hermann Goering ?",
            "What actor and actress have made the most movies ?",
            "What actor came to dinner in Guess Who 's Coming to Dinner ?",
            "What actor dressed up as Santa Claus and had a once-a-year affair with actress Shelley Winters every Christmas for many years ?",
            "What actor first portrayed James Bond ?",
            "What actor has a tattoo on his right wrist reading Scotland Forever ?",
            "What actor learned to play the saxophone and speak Russian for a role in a movie ?",
            "What actor married John F. Kennedy 's sister ?",
            "What actor said in A Day at the Races : `` Either he 's dead or my watch has stopped '' ?",
            "What actor starred in 1980 's Blue Lagoon , 1982 's The Pirate Movie and 1983 's A Night in Heaven ?",
            "What actor was the first man to appear on the cover of McCall 's ?",
            "What actress 's autobiography is titled Shelley : Also Known as Shirley ?",
            "What actress has received the most Oscar nominations ?",
            "What actress holds the record for the most appearances on the cover of Life ?",
            "What actress starred in `` The Lion in Winter '' ?",
            # "What apostle is Taylor Caldwell 's Great Lion of God ?",
            # "What appointments secretary to Richard Nixon went to jail ?",
            # "What architect originated the glass house designed the Chicago
            # Federal Center had a philosophy of `` less is more , '' and produced plans that were the forerunner of the California ranch house ?",
            # "What are Arnold Palmer 's fans called ?",
            "What are names of two old men who appear in the serial tv Muppets Show ?",
            "What are the characters ' names in the Scooby-Doo cartoon ?",
            "What are the first names of Rowan and Martin , the stars of TV 's Laugh-In ?",
            "What are the first names of the famous husband-and-wife acting team of Lunt and Fontanne ?",
            "What are the names of Jack 's original roommates on Three 's Company ?",
            "What are the names of Jacques Cousteau 's two sons ?",
            "What are the names of Richard Nixon 's two daughters ?",
            "What are the top boy names in the U.S. ?",
            "What are the top ten most common girl names in the US ?",
            "What artist 's studio was the Bateau-Lavoir in Montmartre ?",
            #   "What astronomer-architect designed the present St. Paul 's
            #   Cathedral in London ?",
            #   "What athlete makes the most money from sports merchandise sales ?",
            #   "What attorney-general ordered the closing of Alcatraz ?",
            #   "What attorneys work for The Center for the Defense of Free
            #   Enterprise ?",
            "What author did photographer Yousuf Karsh call `` the shiest man I ever met '' ?",
            "What author landed a 468-pound marlin without harness in the early 193 's ?",
            "What author of the Days of Our Lives Cookbook signed on in 198 as Liz Chandler in TV 's Days of Our Lives ?",
            "What author was appointed U.S. ambassador to Spain in 1842 ?",
            # "What barroom judge called himself The Law West of the Pecos ?",
            # "What baseball great plugged Mr. Coffee ?",
            # "What baseball player was known as Charley Hustle ?",
            # "What baseball player was walked the most times ?",
            # "What baseball star turned down a $1 , 000-a-year contract because
            # he felt he had n't earned it ?",
            #  "What baseball team owner and sailor is known as The Mouth of the
            #  South ?",
            #  "What basketball player is credited with 23 , 924 rebounds ?",
            #  "What bestselling modern poet was the co-founder of the famous City Lights Bookshop in San Francisco ?",
            "What bottled-up TV character was born in Baghdad ?",
            #  "What boxer 's life story is titled Raging Bull ?",
            #  "What buxom blonde appeared on the cover of more than 5 magazines ?",
            "What celebrity couple , when going through a divorce , divided their toilet paper into two equal piles ?",
            "What character did Tex Avery first create upon arriving at MGM ?",
            "What character in The Beverly Hillbillies has the given names Daisy Moses ?",
            "What character narrates Treasure Island ?",
            #    "What cheery fellow got the ZIP code 9971 from the U.S. Postal
            #    Service in 1963 ?",
            #    "What cigar-chewing comedian observed : `` You 're only as old as
            #    the woman you feel '' ?",
            #    "What classical Spanish writer warned : `` All that glitters is not gold '' ?",
            #    "What comedian created a punch-drunk pugilist named Cauliflower
            #    McPugg ?",
            #    "What comedian has a legendary reputation for stealing jokes ?",
            #    "What comedian hit the TV screen in 1951 with the NBC afternoon
            #    show Time for Ernie ?",
            #  "What comedian was The Perfect Fool ?",
            #  "What comedian was banned from the Ed Sullivan Show for allegedly
            #  making an obscene gesture at the show 's host ?",
            #  "What comedian was born Allen Stewart Konigsberg ?",
            # "What comedienne calls her sister-in-law Captain Bligh and her
            # mother-in-law Moby Dick ?",
            # "What comedienne upstaged Dwight D. Eisenhower 's first
            # inauguration by giving birth to her first child ?",
            # "What comic of TV 's golden age went by the motto `` Anything for a laugh '' ?",
            # "What composer was awarded the Medal of Honor by Franklin D.
            # Roosevelt ?",
            # "What contemptible scoundrel stole the cork from my lunch ?",
            # "What costume designer decided that Michael Jackson should only
            # wear one glove ?",
            # "What count did Alexandre Dumas write about ?",
            # "What creative genius said : `` Everything comes to him who hustles while he waits '' ?",
            # "What crooner joined The Andrews Sisters for Pistol Packin Mama ?",
            "What daughter of Henry VIII and Anne Boleyn became queen of England ?",
            # "What department store heir is responsible for raising a three-ton
            # safe from the underwater wreckage of the Andrea Doria ?",
            #  "What detective lives on Punchbowl Hill and has 11 children ?",
            #   "What dictator has the nickname `` El Maximo '' ?",
            #    "What diminutive American female gymnast stole the show at the 1984 Olympics ?",
            #    "What director made one silent and one sound version of The Ten
            #    Commandments ?",
            #    "What director portrayed the commandant of the POW camp in 1953 's
            #    Stalag 17 ?",
            #    "What doctor claimed in a 1946 book : `` There is no such thing as
            #    a bad boy '' ?",
            #     "What doctor is synonymous with footwear and foot care ?",
            #     "What double talking `` professor '' holds a doctorate in Nothing ?",
            "What dumb-but-loveable character did Maurice Gosfield play on The Phil Silvers Show ?",
            #     "What dummy received an honorary degree from Northwestern
            #     University ?",
            #    "What engineer invented the pull-tab can ?",
            #    "What enigmatic U.S. vice president was once tried and acquitted
            #    for treason in a plot to set up his own independent empire in the West ?",
            #    "What explorer was nicknamed Iberia 's Pilot ?",
            #    "What explorers followed Columbus to the Americas ?",
            #    "What famed clown appeared on an early Howdy Doody Show and
            #    insisted that Clarabell be made up as a real clown ?",
            "What famous British actor lost his voice after an operation in 1966 ?",
            #    "What famous New York City mayor wrote the hit song , `` Will You
            #    Love Me in December as You Do in May ? ''",
            "What famous actress made her first appearance on stage at the age of five in the year 191 as `` Baby '' ?",
            #   "What famous coach said `` if you can 't beat 'em in the alley ,
            #   you can 't beat 'em on the ice '' ?",
            #   "What famous comedian recently tried without success to revive the
            #   play ?",
            "What famous comic strip character died of acne ?",
            "What famous communist leader died in Mexico City ?",
            #   "What famous film and TV cowboy lent his name to a fast food chain ?",
            #   "What famous husband-and-wife team did radio ads for Blue Nun wine ?",
            #   "What famous male vocalist has the same name as the composer of the opera Hansel and Gretel ?",
            #   "What famous model was married to Billy Joel ?",
            #   "What famous singing cowboy owns the California Angels baseball
            #   team ?",
            #   "What famous soldier was born in Europe , died in Asia , and was
            #   laid to rest in Africa ?",
            #   "What father and son won the Medal of Honor ?",
            #   "What feathered cartoon characters do Yugoslavians know as Vlaja ,
            #   Gaja , and Raja ?",
            #   "What female faith healer wrote the inspirational book I Believe in Miracles ?",
            #   "What female painter produced primitives of rural New England life ?",
            #   "What female suspect in the game of Clue is single ?",
            #   "What feminist wrote Sexual Politics and Flying ?",
            "What fictional character is known as the `` melancholy Dane '' ?",
            "What first name was Nipsy Russell given at birth ?",
            #    "What fool is not so wise To lose an oath to win a paradise ?",
            #    "What football coach 's story was told in the movie Run to Daylight ?",
            "What former African leader held his country 's boxing title for nine years ?",
            #    "What former major-league left-handed baseball pitcher was known as `` Space Man '' ?",
            "What former president 's daughter has written a book titled Murder in the White House ?",
            "What fruit-topped actress was known as The Brazilian Bombshell ?",
            "What future President became Senate majority whip under Harry Truman ?",
            #     "What future Soviet dictator was training to be a priest when he
            #     got turned on to Marxism ?",
            #    "What future deer hunter portrayed Annie Hall 's neurotic brother , Duane ?",
            "What girl 's name is `` Teddy '' an affectionate form of ?",
            #    "What golfer has been called Ohio Fats and Blobbo ?",
            #    "What hard-of hearing artist painted Sunflowers ?",
            "What has been the most common Christian name of U.S. presidents ?",
            #    "What heavyweight boxer was known as The Wild Bull of the Pampas ?",
            #    "What hockey player did Ronald Reagan joke he would swap Texas for ?",
            #    "What ill-fated American general dragged a bull terrier named
            #    Willie through World War II ?",
            "What is Alice Cooper 's real name ?",
            "What is Dr. Ruth 's last name ?",
            "What is Drew Barrymore 's middle name ?",
            "What is Goldfinger 's first name ?",
            "What is Jimmy Olsen 's full name ?",
            "What is Li 'l Abner 's last name ?",
            "What is Michael Jackson 's father 's name ?",
            "What is Michael Jackson 's middle name ?",
            # "What is Nathan Hamill 's role in the new Star Wars prequel ?",
            "What is Rona Barrett 's married name ?",
            "What is Shakespeare 's nickname ?",
            "What is Supergirl 's secret identity ?",
            "What is a person called that likes fire ?",
            "What is her husband 's name ?",
            "What is the Viking Prince 's first name ?",
            "What is the full name of the man who invented the multicolored game cube that has 42.3 quintillion potential combinations ?",
            "What is the last name of Lucy and Linus from the Peanut 's comic strip ?",
            "What is the most common boy 's or girl 's name ?",
            "What is the most common name ?",
            "What is the most popular last name ?",
            "What is the name of Dolly Parton 's rarely seen husband ?",
            "What is the name of Miss India 1994 ?",
            "What is the name of Neil Armstrong 's wife ?",
            "What is the name of a Greek god ?",
            "What is the name of actor Rex Harrison 's son , who starred in a modestly popular TV show during the late 1960's ?",
            "What is the name of the American swimmer who won seven gold medals in the 1972 Olympics ?",
            "What is the name of the American who was captured when his plane went down over Syrian-held Lebanon ?",
            "What is the name of the Indian who became prime minister by beating Mrs. Gandhi in the 1977 election ?",
            "What is the name of the brilliant British economist behind its creation ?",
            "What is the name of the deranged super-criminal Otto Octavius uses ?",
            "What is the name of the inventor of silly putty ?",
            "What is the name of the leader of Ireland ?",
            "What is the name of the managing director of Apricot Computer ?",
            "What is the name of the police officer who tried to keep order in Top Cat 's neighborhood ?",
            "What is the name of the pop singer whose song became the theme song for a brand of catsup ?",
            "What is the name of the president of Garmat U.S.A ?",
            "What is the name of the woman who was with John Belushi when he died ?",
            "What is the nickname of the famous flyer who mistakenly flew to Ireland instead of to Los Angeles ?",
            #  "What is the present Pope named ?",
            "What is the protagonist 's name in Dostoevski 's `` The Idiot '' ?",
            "What is the real name of disc jockey `` Wolfman Jack '' ?",
            "What is the real name of the singer , Madonna ?",
            #   "What jockey won 17 Triple Crown races ?",
            #   "What journalist can be found in and around Walden Puddle ?",
            #   "What kind of women gave Sigmund Freud erotic dreams ?",
            "What king boycotted Prince Charles 's wedding ?",
            "What king is satirized in the line : `` The King was in the countinghouse , counting all his money '' ?",
            "What king was forced to agree to the Magna Carta ?",
            "What knighted actor narrates TV 's The World at War ?",
            "What labor leader was last seen in the parking lot of a Michigan restaurant ?",
            #  "What lawyer won the largest divorce settlement , $85 million , in U.S. history for Sheika Dena Al-Farri ?",
            "What little boy and dog live in a shoe ?",
            #  "What longtime game show host dropped dead while jogging in
            #  Central Park in 1984 ?",
            #  "What major Victorian novelist spent as much time working for
            #  the post office as he did writing ?",
            #  "What mayor made so many TV appearances he was asked to join
            #  AFTRA in 1984 ?",
            #  "What member of The Little Rascals has an on-again , off-again
            #  sweetheart in Darla Hood ?",
            #  "What monarch signed the Magna Carta ?",
            #  "What multitalented Academy-award-winning director failed a
            #  college course in motion-picture production ?",
            #  "What mustachioed comedian portrayed Frankie in North to Alaska ?",
            #  "What mystery writer penned `` ...the glory that was Greece ,
            #  and the grandeur that was Rome '' ?",
            #  "What mythical figure carries an hourglass and a scythe ?",
            #   "What name does the world know Renaissance artist Kyriakos
            #   Theotokopoulos by ?",
            #   "What non-conformist abstract painter was dubbed Jack The
            #   Dripper by Time ?",
            "What one of the Backstreet Boys are single ?",
            #  "What onetime member of Ronald Reagan 's cabinet called federal policy toward Indians `` an example of the failure of socialism '' ?",
            #  "What painter popularized soup cans and Brillo soap pad boxes ?",
            #  "What part did Benjamin Franklin play in the development of the newspaper in America ?",
            #  "What part did John Peter Zenger play in the deveopment of the
            #  newspaper in America ?",
            "What person 's head is on a dime ?",
            #   "What pillar of the Dutch Renaissance painted Aristotle
            #   Contemplating the Bust of Homer ?",
            #   "What player squats an average of 3 times during a baseball
            #   doubleheader ?",
            #   "What poet wrote : `` ... I have promises to keep , and miles
            #   to go before I sleep '' ?",
            "What president 's ghost is said to haunt the White House ?",
            "What president also became a supreme court justice ?",
            "What president kissed the Queen Mother on the lips ?",
            #  "What presidential press secretary dismissed Watergate as a
            #  third-rate burglary attempt ?",
            # "What professional cricketer 's son wrote The War of the Worlds in 1898 ?",
            # "What pseudonym did William Sydney Porter use in writing The
            # Gift of the Magi ?",
            "What radio , TV and movie character did Jackie Gleason and William Bendix play ?",
            # "What relative of Leo Tolstoy translated War and Peace eight
            # times ?",
            "What robust U.S. President imported his own instructor after seeing a judo match ?",

            #            "What singer 's hit song inspired the Dolly Parton Stallone
            #            movie Rhinestone ?",
            #           "What singer 's theme song was When the Moon Comes over the
            #           Mountain ?",
            #          "What singer became despondent over the death of Freddie Prinze , quit show business , and then quit the business ?",
            #         "What singer sings `` Oh Boy '' ?",
            #        "What six-foot temperance advocate wielded her hatchet on
            #        saloons ?",
            "What son of a 15-year-old Mexican girl and a half-Irish father became the world 's most famous Greek ?",
            #       "What spy novelist served as Moscow correspondent for Reuter
            #       and The Times of London ?",
            #      "What suburban housewife and mother of three wrote The Feminine Mystique ?",
            #     "What tennis player has the nickname `` Nasty '' ?",
            #    "What two New York Yankee pitchers swapped wives and families ?",
            #   "What two US biochemists won the Nobel Prize in medicine in
            #   1992 ?",
            #  "What two baseball players make up the battery ?",
            # "What two commanders directed the forces in the Battle of El
            # Alamein ?",
            # "What two historical figures , who fought each other in a
            # famous battle , each have a food named after them ?",
            "What two presidents of the U.S. published books of poetry ?",
            # "What video game hero do some of his fans call Chomper ?",
            "What was Al Capone 's nickname ?",
            "What was American folk hero John Chapman 's nickname ?",
            "What was Darth Vader 's son named ?",
            "What was Fred Astaire 's dancing partner 's name ?",
            "What was J.F.K. 's wife 's name ?",
            "What was Mao 's second name ?",
            "What was Mao , the Chinese leader 's , full name ?",
            "What was Marilyn Monroe 's real name ?",
            "What was Michelangelo 's last name ?",
            "What was Thatcher 's first name ?",
            "What was W.C. Fields ' real name ?",
            "What was William F. Cody 's better-known name ?",
            "What was football star Elroy Hirsch 's nickname ?",
            "What was her real name ?",
            "What was the Christian name of the title character in Our Miss Brooks ?",
            #   "What was the infamous pseudonym of Peter Sutcliffe ?",

            "What was the man 's name who was killed in a duel with Aaron Burr ?",
            "What was the name of Darth Vader 's son ?",
            "What was the name of Randy Craft 's lawyer ?",
            "What was the name of Randy Steven Craft 's lawyer ?",
            "What was the name of `` The Muppets '' creator ?",
            "What was the name of the Titanic 's captain ?",
            "What was the name of the US helicopter pilot shot down over North Korea ?",
            "What was the name of the cook on Rawhide ?",
            "What was the name of the daughter of the Virginia chief Powhatan that married John Rolfe ?",
            "What was the name of the director of the movie `` Jaws '' ?",
            "What was the name of the first Russian astronaut to do a spacewalk ?",
            "What was the name of the first Watergate special prosecutor , later fired by Nixon ?",
            "What was the name of the lawyer who represented Randy Craft ?",
            "What was the name of the lawyer who represented Randy Steven Craft ?",
            "What was the nickname of Frederick I , Holy Roman Emperor and King of Germany ?",
            "What was the nickname of German flying ace Manfred von Richthofen ?",
            "What was the nickname of model Leslie Hornby ?",
            "What was the player 's name who played nose tackle for the Eagles in Super Bowl XV ?",
            "What was the real name of writer Ross Macdonald , creator of the hero Lew Archer ?",
            #   "What was the role of the Medieval Guild ?",
            # "What well-known TV talk show host was a lay preacher by the
            # time he was seventeen ?",
            "What well-known actor is the father of star Alan Alda ?",
            # "What well-known music personality is the father of an adopted
            # son named Hans Christian Henderson ?",
            "What were Babe Ruth 's Christian names ?",
            "What were the last names of gangsters Bonnie and Clyde ?",
            #  "What wild and crazy guy wrote a book called Cruel Shoes ?",
            "What woman has carried the most multiple births , twins , triplets , etc. , ?",
            "What woman pitcher has struck out Ted Williams and Hank Aaron ?",
            "What woman was Time 's Man of the Year for 1952 ?",
            # "What wrestling star became `` The Incredible Hulk '' ?",
            # "What writer is famous for physically putting himself into the
            # center of his subject matter ?",
            # "What writer-journalist made his mark describing colorful
            # Broadway and underworld characters ?",
            # "When Mighty Mouse was conceived , what was his original name ?",
            # "When called upon to surrender , what American general replied
            # , `` Sir , I have not yet begun to fight . '' ?",
            # "Which Bloom County resident wreaks havoc with a computer ?",
            "Which Bourbon king was restored to the French throne during Napoleon 's abdication ?",
            "Which Doonesbury character was likely to turn into a werewolf ?",
            "Which German president was pressured into appointing Hitler chancellor in 1933 ?",
            # "Which NBA players had jersey number 0 ?",
            # "Which Rockefeller was sometimes called `` JDR3 '' ?",
            "Which U.S. President is buried in Washington , D.C. ?",
            "Which U.S.A. president appeared on `` Laugh-In '' ?",
            # "Which Vietnamese terrorist is now a UN delegate in Doonesbury ?",
            # "Which classical Spanish writer said `` All that glitters is
            # not gold '' ?",
            # "Which comedian 's signature line is `` Can we talk '' ?",
            # "Which former Ku Klux Klan member won an elected office in the
            # U.S. ?",
            "Which glamorous actress is a close friend of Dick Tracy ?",
            # "Which is the only Dick Tracy villain to appear three times ?",
            "Which king signed the Magna Carta ?",
            "Which member of Charlie 's Angels sang vocals for Josie and the Pussycats ?",
            "Which member of the Micronauts spent 1 years traveling the Microverse in the Marvel comics ?",
            #   "Which of the Seven Dwarfs comes first alphabetically ?",
            #   "Which of the following TV newsmen was a Rhodes scholar ?",
            "Which of the following actors worked in New York 's Yiddish Theater ?",
            "Which of the following celebrities started his show-biz career as a disc jockey ?",
            "Which of the following celebrities was not born in Philadelphia ?",
            #    "Which of the following did not receive a 1983 `` Outstanding
            #    Mother Award '' from the National Mother 's Day Committee ?",
            #  "Which of the following famous people does not paint as a hobby ?",
            #  "Which of the following men was not married to Rita Hayworth ?",
            #  "Which of the following people is not associated with Andy
            #  Warhol ?",
            #   "Which of the following rock 'n roll stars has a `` star '' on
            #   Hollywood Boulevard ?",
            #   "Which of the following was Rhodes Scholar ?",
            #    "Which of these are authors ?",
            #   "Which one of the original seven Mercury program astronauts did not fly on any of the Mercury flights ?",
            "Which president was unmarried ?",
            "Which presidents of the USA were Masons ?",
            #   "Which two inventors invented Post-its ?",
            "Who 's The King of Swing ?",
            "Who 's baby was Sweet Pea on the Popeye cartoon ?",
            "Who 's played the most games for the New York Yankees ?",
            "Who 's the founder and editor of The National Review ?",
            "Who 's the lead singer of the Led Zeppelin band ?",
            "Who 's the only U.S. president to have won a Pulitzer Prize ?",
            "Who 's the only man to have won the Olympic decathlon twice ?",
            "Who 's the only president buried in Washington",
            "Who 's the twin brother of the Greek goddess Artemis ?",
            "Who 's won the most Oscars for costume design ?",
            "Who accompanied Space Ghost on his missions ?",
            "Who advised listeners to `` see the U.S.A. in your Chevrolet '' ?",
            "Who appointed the chair of the Federal Reserve ?",
            "Who are Woody Woodpecker 's niece and nephew ?",
            "Who are the presidents of Mexico and Indonesia ?",
            "Who are the top 10 richest people in the world ?",
            "Who are the top ten richest people in the world ?",
            "Who are the two sons of Ozzie and Harriet Nelson ?",
            "Who asked the musical question : `` Have you ever been to electric lady land ? ''",
            "Who asked you to do the Loco-Motion with her in 1962 ?",
            "Who awarded The Flying Fickle Finger of Fate ?",
            "Who banned Peter Rose from baseball for betting on games ?",
            "Who became president of the U.S. in 1789 ?",
            "Who bestowed great power upon Captain Britain ?",
            "Who betrayed Norway to the Nazis ?",
            "Who built the first successful stern wheel steamboat ?",
            "Who came up with the name , El Nino ?",
            "Who claimed he killed 4 , 280 buffalo as food for the crew building the Kansas Pacific Railway ?",
            "Who claimed to be the world 's most perfectly-developed man ?",
            "Who claims to have the greatest show on earth ?",
            "Who co-starred with Julie Andrews in Mary Poppins ?",
            "Who coined the term NN cyberspace `` in his novel NN Neuromancer '' ?",
            "Who commanded the French forces at the Battle of Orleans ?",
            "Who comprised the now-defunct comic book team known as the Champions ?",
            "Who created Big Ben ?",
            "Who created Billy Pilgrim , a survivor of the Dresden firestorm ?",
            "Who created Dennis the Menace ?",
            "Who created Harry Lime ?",
            "Who created Maudie Frickett ?",
            "Who created `` The Muppets '' ?",
            "Who created private detective Philip Marlowe ?",
            "Who created the Fantastic Four , Hulk , and Thor ?",
            "Who created the World Wide Web , WWW ?",
            "Who created the character James Bond ?",
            "Who created the character of Scrooge ?",
            "Who created the comic strip , `` Garfield '' ?",
            "Who created the monster in Mary Shelley 's novel Frankenstein ?",
            "Who danced into stardom with Fred Astaire in 1941 's You 'll Never Get Rich ?",
            "Who declared : `` I am down on whores and I shan 't stop ripping them '' ?",
            "Who declared : `` I think I 'll go out and milk the elk '' ?",
            "Who delivered his last newscast on March 6 , 1981 ?",
            "Who designed London Bridge ?",
            "Who developed potlatch ?",
            "Who developed the Macintosh computer ?",
            "Who developed the first polio vaccine ?",
            "Who developed the vaccination against polio ?",
            "Who did Arthur H. Bremer try to assassinate on May 15 , 1972 ?",
            "Who did Bobby Fischer beat to win the world chess championship ?",
            "Who did Dita Beard work for ?",
            "Who did Doris Day mean when she said : `` I call him Ernie because he 's certainly no Rock '' ?",
            "Who did Jackie Kennedy commission to write The Death of a President ?",
            "Who did Napolean defeat at Jena and Auerstadt ?",
            "Who did Richard Nixon tender his resignation to ?",
            "Who did Sara Jane Moore try to assassinate ?",
            "Who did Sonny Liston succeed as world heavyweight boxing champion ?",
            "Who did the Seven Mules block for ?",
            "Who died 1 feet from where John F. Kennedy did ?",
            "Who died with more than 1 , 000 U.S. patents to his credit ?",
            "Who directed Citizen Kane ?",
            "Who directed The Wild Bunch ?",
            "Who directed `` Jaws '' ?",
            "Who directed the first Woody Woodpecker cartoon ?",
            "Who discovered America ?",
            "Who discovered electricity ?",
            "Who discovered imaginary numbers ?",
            "Who discovered oxygen ?",
            "Who discovered radium ?",
            "Who discovered x-rays ?",
            "Who do Herb and Tootsie live next door to ?",
            "Who does Shakespeare 's Antonio borrow 3 , 0 ducats from ?",
            "Who does data collection in tourism ?",
            "Who does the advertizing for Frito-Lay ?",
            "Who does the voices of the Simpsons ?",
            "Who domesticated the wild turkey ?",
            "Who earns their money the hard way ?",
            "Who else was considered for the role of Luke Skywalker when George Lucas was casting for Star Wars ?",
            "Who established a Viking colony in Greenland about 985 ?",
            "Who famously rode to warn the people of Massachusetts that the British were coming ?",
            "Who fired Maria Ybarra from her position in San Diego council ?",
            "Who first broke the sound barrier ?",
            "Who followed Caesar ?",
            "Who followed Willy Brandt as chancellor of the Federal Republic of Germany ?",
            "Who followed up his first two underwater thrillers with The Girl of the Sea of Cortez ?",
            "Who found Hawaii ?",
            "Who founded American Red Cross ?",
            "Who founded the People 's Temple Commune ?",
            "Who founded the Unification Church ?",
            "Who founded the first aerodynamics laboratory in 1912 ?",
            "Who founded the modern theory of probability ?",
            "Who gave Abbie Hoffman his first dose of LSD ?",
            "Who gave King Arthur the round table ?",
            "Who gave us the `` Rolling Writer '' ?",
            "Who graced the airwaves with such pearls as `` Do ya lo-o-ove me ? Get naked , baby ! '' ?",
            "Who has more DNA - a man or a woman ?",
            "Who has the only speaking role in `` Silent Movie '' ?",
            "Who headed Hitler 's infamous Gestapo ?",
            "Who held the endurance record for women pilots in 1929 ?",
            "Who holds the NFL record for most touchdowns in a season ?",
            "Who holds the career record for the most major league home runs ?",
            "Who invented Astroturf ?",
            "Who invented Make-up ?",
            "Who invented Trivial Pursuit ?",
            "Who invented `` The Muppets '' ?",
            "Who invented baseball ?",
            "Who invented basketball ?",
            "Who invented batteries ?",
            "Who invented panties ?",
            "Who invented silly putty ?",
            "Who invented television ?",
            "Who invented the Moog Synthesizer ?",
            "Who invented the Wonderbra ?",
            "Who invented the calculator ?",
            "Who invented the electric guitar ?",
            "Who invented the fax machine ?",
            "Who invented the fountain ?",
            "Who invented the game Scrabble ?",
            "Who invented the game bowling ?",
            "Who invented the horoscope ?",
            "Who invented the hula hoop ?",
            "Who invented the instant Polaroid camera ?",
            "Who invented the lawnmower ?",
            "Who invented the paper clip ?",
            "Who invented the process to make condensed milk ?",
            "Who invented the pull-tab opener on cans ?",
            "Who invented the radio ?",
            "Who invented the road traffic cone ?",
            "Who invented the slinky ?",
            "Who invented the stethoscope ?",
            "Who invented the stock ticker in 1870 ?",
            "Who invented the telephone ?",
            "Who invented the toothbrush ?",
            "Who invented the vacuum cleaner ?",
            "Who invented volleyball ?",
            "Who is Archie Bunker 's son-in-law ?",
            "Who is Karenna Gore , Al Gore 's oldest daughter , married to ?",
            "Who is King in Alley Oop 's home of Moo ?",
            "Who is Luke Skywalker 's father ?",
            "Who is Malaysia 's 43rd prime minister ?",
            "Who is Mia Farrow 's mother ?",
            "Who is Olive Oyl 's brother ?",
            "Who is Pia Zadora 's millionaire husband and mentor ?",
            "Who is Rocky 's and Bullwinkle 's ever-lost friend ?",
            "Who is Snoopy 's arch-enemy ?",
            "Who is Westview High 's band director in Funky Winkerbean ?",
            "Who is a German philosopher ?",
            "Who is actress Goldie Hawn 's current actor boyfriend ?",
            "Who is always trying to get the rent from Andy Capp ?",
            "Who is behind the name of the Harvey Wallbanger drink ?",
            "Who is buried in the great pyramid of Giza ?",
            "Who is considered The First Lady of the American Stage ?",
            "Who is currently the most popular singer in the world ?",
            "Who is known as `` the world 's oldest teenager '' ?",
            "Who is reputed to be the greatest maker of violins ?",
            "Who is section manager for guidance and control systems at JPL ?",
            "Who is stationed at Camp Swampy in the comic strips ?",
            "Who is the Antichrist ?",
            "Who is the French literary charcter who is chiefly famous for his enormous nose ?",
            "Who is the Greek God of the Sea ?",
            "Who is the Incredible Hulk in reality ?",
            "Who is the Pope ?",
            "Who is the President of Ghana ?",
            "Who is the President of Pergament ?",
            "Who is the Prime Minister of Canada ?",
            "Who is the Prophet of Medina ?",
            "Who is the Queen of Holland ?",
            "Who is the Voyager project manager ?",
            "Who is the actress Bette Davis once said she wished she looked like ?",
            "Who is the actress known for her role in the movie `` Gypsy '' ?",
            "Who is the author of the book , `` The Iron Lady : A Biography of Margaret Thatcher '' ?",
            "Who is the best known villain of the 165 Gunpowder Plot ?",
            "Who is the composer of `` Canon in D Major '' ?",
            "Who is the congressman from state of Texas on the armed forces committee ?",
            "Who is the creator of `` The Muppets '' ?",
            "Who is the current UN Secretary General ?",
            "Who is the current prime minister and president of Russia ?",
            "Who is the director and editor of the movie Big starring Tom Hanks ?",
            "Who is the director of intergovernmental affairs for the San Diego county ?",
            "Who is the director of the international group called the Human Genome Organization , HUGO , that is trying to coordinate gene-mapping research worldwide ?",
            "Who is the famous movie star who also acted as sewer commissioner of Provo Canyon , Utah ?",
            "Who is the famous sister of actress Olivia De Havilland ?",
            "Who is the fastest guitarist ?",
            "Who is the fastest swimmer in the world ?",
            "Who is the father of the computer ?",
            "Who is the founder of Scientology ?",
            "Who is the governor of Alaska ?",
            "Who is the head of the World Bank ?",
            "Who is the leader of Brunei ?",
            "Who is the leader of India ?",
            "Who is the man behind the pig-the man who pulls the strings and speaks for Miss Piggy ?",
            "Who is the mathematician that won the Noble Prize for Literature in 1950 ?",
            "Who is the mayor of Marbella ?",
            "Who is the monarch of the United Kingdom ?",
            "Who is the most sexy celebrity ?",
            "Who is the nebbish that is Marvel 's official mascot ?",
            "Who is the one Independent Member of Congress ?",
            "Who is the only president to serve 2 non-consecutive terms ?",
            "Who is the only prime minister of Canada to serve 22 years but not necessarily consecutively ?",
            "Who is the owner of CNN ?",
            "Who is the premier of China ?",
            "Who is the president of Bolivia ?",
            "Who is the president of Stanford University ?",
            "Who is the president of the Spanish government ?",
            "Who is the prime minister in Norway ?",
            "Who is the prime minister of Australia ?",
            "Who is the prime minister of Japan ?",
            "Who is the prophet of the religion of Islam ?",
            "Who is the prophet that is most connected to the Dead Sea ?",
            "Who is the richest person in the world , without owning a business ?",
            "Who is the richest person in the world ?",
            "Who is the richest woman in the world ?",
            "Who is the sexiest women in the world ?",
            "Who is the son-in-law of Sen. Everett Dirkson who was also a senator in the '70 's ?",
            "Who is the superstar in rent-a-cars ?",
            "Who is the tallest man in the world ?",
            "Who is the voice of Miss Piggy ?",
            "Who is the worst US President ever ?",
            "Who is the youngest of the Beatles ?",
            "Who kept the most famous diary in the English language ?",
            "Who killed Caesar ?",
            "Who killed Gandhi ?",
            "Who killed JFK ?",
            "Who killed John F. Kennedy ?",
            "Who killed Kurt Cobain ?",
            "Who killed Lee Harvey Oswald ?",
            "Who killed Martin Luther King ?",
            "Who killed more people , Hitler or Stalin ?",
            "Who leads the star ship Enterprise in Star Trek ?",
            "Who led the Normans to victory in the Battle of Hastings ?",
            "Who led the opposition when Konrad Adenauer was Chancellor in Germany ?",
            "Who liberated 19th century Sicily and Naples ?",
            "Who lived in the Neuschwanstein castle ?",
            "Who lived on the shores of the Gitchee Gumee River ?",
            "Who lives at 24 Sussex Drive , Ottawa ?",
            "Who lives at 39 Stone Canyon Way ?",
            "Who loved Flash Gordon besides Dale ?",
            "Who made Stonehenge ?",
            "Who made a boat out of gopher wood ?",
            "Who made the deodorant that claimed that it `` actually builds up resistance to odor '' ?",
            "Who made the first gas engine ?",
            "Who made the first surfboard ?",
            "Who made the most appearances in the center square on Hollywood Squares ?",
            "Who made the musical plea Be True to Your School ?",
            "Who makes chicken `` finger lickin '' good ?",
            "Who makes the `` Die Hard '' car battery ?",
            "Who makes the `` cross-your-heart bra '' ?",
            "Who markets Spaghetti-o 's ?",
            "Who moderated the first Kennedy-Nixon TV debate ?",
            "Who murdered Leno and Rosemary LaBianca on August 1",
            "Who owns CNN ?",
            "Who owns the St. Louis Rams ?",
            "Who owns the rights on a TV program ?",
            "Who painted Mother and Child ?",
            "Who painted `` Soft Self-Portrait with Grilled Bacon '' ?",
            "Who painted the Sistine Chapel ?",
            "Who painted the ceiling of the Sistine Chapel ?",
            "Who patented the first phonograph ?",
            "Who penned : `` Neither a borrower nor a lender be '' ?",
            "Who played Al Jolson in the Jolson Story ?",
            "Who played Emperor Palpatine in Star Wars ?",
            "Who played Humpty Dumpty in the 1933 film Alice in Wonderland ?",
            "Who played Lucas McCain on The Rifleman ?",
            "Who played Maria in the film West Side Story ?",
            "Who played Sally Rogers on The Dick Van Dyke Show ?",
            "Who played for the Chicago Bears , Houston Oilers and Oakland Raiders in a 26-year pro football career ?",
            "Who played the Ringo Kid in the 1939 film Stagecoach ?",
            "Who played the father on `` Charles in Charge '' ?",
            "Who played the original Charlie 's Angels ?",
            "Who played the part of the Godfather in the movie , ` The Godfather ' ?",
            "Who played the title role in I Was a Teenage Werewolf ?",
            "Who played the title role in My Favorite Martian ?",
            "Who played the title role in The Romantic Englishwoman ?",
            "Who plays shortstop for Charlie Brown 's baseball team ?",
            "Who plays the cop in the movie `` Kindergarten Cop '' ?",
            "Who portrayed Carl Bernstein in All the President 's Men ?",
            "Who portrayed Dracula in Hammer Studios ' films ?",
            "Who portrayed Etta Place , companion to Butch Cassidey and the Sundance Kid ?",
            "Who portrayed Fatman in the television show , `` Jake and the Fatman '' ?",
            "Who portrayed Field Marshal Erwin Rommel in The Desert Fox ?",
            "Who portrayed George M. Cohan in 1942 's Yankee Doodle Dandy ?",
            "Who portrayed Maggio in the film From Here to Eternity ?",
            "Who portrayed Prewett in From Here to Eternity ?",
            "Who portrayed Renaud in Casablanca ?",
            "Who portrayed Sherlock Holmes in 14 films between 1939 and 1946 ?",
            "Who portrayed The Cowardly Lion in The Wizard of Oz ?",
            "Who portrayed Vincent Van Gogh in Lust for Life ?",
            "Who portrayed W.C. Fields in the film W.C. Fields and Me ?",
            "Who portrayed `` Rosanne Rosanna-Dana '' on the television show `` Saturday Night Live '' ?",
            "Who portrayed `` the man without a face '' in the movie of the same name ?",
            "Who portrayed portly criminologist Carl Hyatt on Checkmate ?",
            "Who portrayed the title character in the film The Day of the Jackal ?",
            "Who protects DC Comics ' realm of dreams ?",
            "Who received the Will Rogers Award in 1989 ?",
            "Who recorded the 1957 hit Tammy ?",
            "Who released the Internet worm in the late 1980s ?",
            "Who replaced Bert Parks as the host of The Miss America Pageant ?",
            "Who replies `` I know '' to Princess Leia 's confession `` I love you '' in The Empire Strikes Back ?",
            "Who reports the weather on the `` Good Morning America '' television show ?",
            "Who retired with 755 home runs to his credit ?",
            "Who runs Andy Capp 's favorite pub ?",
            "Who said , `` I shall return . '' during World War Two ?",
            "Who said : `` Old soldiers never die ; they just fade away '' ?",
            "Who said : `` Soldiers win the battles and generals get the credit '' ?",
            "Who said : `` The victor will never be asked if he told the truth '' ?",
            "Who said : `` What contemptible scoundrel stole the cork from my lunch ? ''",
            "Who said `` Give me liberty or give me death '' ?",
            "Who said `` What contemptible scoundrel stole the cork from my lunch ? ''",
            "Who said `` the only thing we have to fear is fear itself '' ?",
            "Who said of Super Bowl III in 1969 : `` We 'll win- I guarantee it '' ?",
            "Who sang about Desmond and Molly Jones ?",
            "Who sang the song `` Hooked on a Feeling '' in the dancing baby episode of `` Ally Mcbeal '' ?",
            "Who says , `` If you don 't look good , we don 't look good '' ?",
            "Who seized power from Milton Obote in 1971 ?",
            "Who sells Viagra ?",
            "Who sent the brief message `` I came , I saw , I conquered '' ?",
            "Who served as inspiration for the schoolteacher portrayed by Robin Williams in `` Dead Poets Society '' ?",
            "Who shared a New York City apartment with Roger Maris the year he hit 61 home runs ?",
            "Who shoplifts ?",
            "Who shot Billy the Kid ?",
            "Who shot Lee Harvey Oswald ?",
            "Who shot and killed himself while painting Wheatfield with Crows ?",
            "Who should I call to get a tour of the New York Stock Exchange ?",
            "Who sings Angel Eyes from the 80 's ?",
            "Who sings the song `` Drink to me with thine eyes '' by Ben Johnson ?",
            "Who sings the themes for `` Dawson 's Creek '' and `` Felicity '' ?",
            "Who sought to create The Great Society ?",
            "Who spoke the only word in Mel Brooks 's Silent Movie ?",
            "Who starred in Singing in the Rain and The Singing Nun ?",
            "Who starred in the movie The War of the Worlds ?",
            "Who starred with Charlie Chaplin in Modern Times and The Great Dictator ?",
            "Who started the Dominos Pizza chain ?",
            "Who stopped making diary entries on May 31 , 1669 , because he thought he was going blind ?",
            "Who succeeded Nikita Khrushchev as first secretary of the Communist Party ?",
            "Who sued the Dannon yougurt company for using a character named Ron Raider for promotion ?",
            "Who taught Matt Murdock to use his extraordinary abilities in Marvel comics ?",
            "Who thought he 'd never see a poem lovely as a tree ?",
            "Who told all in Ball Four ?",
            "Who took over as conductor of the Boston Pops after Arthur Fiedler 's long reign ?",
            "Who took the toys donated for the Doodyville Orphans ' Fund and kept them for himself ?",
            "Who tramped through Florida looking for the Fountain of Youth ?",
            "Who turned all he touched to gold ?",
            "Who used AuH2O as an election slogan ?",
            "Who was America 's first Public Enemy No. 1 ?",
            "Who was Ben Casey 's boss ?",
            "Who was Bonnie Blue Butler 's father ?",
            "Who was Camp David named for ?",
            "Who was Charles Lindbergh 's wife ?",
            "Who was Darth Vader 's son ?",
            "Who was Garrett Morgan married to ?",
            "Who was Gerald Ford 's vice president ?",
            "Who was Hitler 's minister of propaganda ?",
            "Who was International Olympic Committee chairman at the 1936 Summer Games ?",
            "Who was Israel 's first prime minister ?",
            "Who was Lauren Bacall 's first husband ?",
            "Who was President Cleveland 's wife ?",
            "Who was President of Afghanistan in 1994 ?",
            "Who was President of Costa Rica in 1994 ?",
            "Who was Randy Steven Craft 's lawyer ?",
            "Who was Samuel Johnsons 's friend and biographer ?",
            "Who was Scrooge 's dead partner in Dickens 's A Christmas Carol ?",
            "Who was Secretary of State during the Nixon administration ?",
            "Who was Shakespeare 's Moorish general ?",
            "Who was Sherlock Holmes 's archenemy ?",
            "Who was The Pride of the Yankees ?",
            "Who was Tiny Tim 's father ?",
            "Who was actress June Havoc 's legendary sister ?",
            "Who was chairman of the Senate select committee that tried to get to the bottom of Watergate ?",
            "Who was chief engineer of the Starship Enterprise ?",
            "Who was chosen to be the first black chairman of the military Joint Chiefs of Staff ?",
            "Who was considered to be the father of psychology ?",
            "Who was credited with saying : `` I never met a man I did n't like '' ?",
            "Who was elected president of South Africa in 1994 ?",
            "Who was in Death of a Salesman original movie , not 1985 ?",
            "Who was known as the Time Master in comic books ?",
            "Who was made the first honorary citizen of the U.S. ?",
            "Who was named Admiral of the Ocean Seas and Viceroy and Governor General of all the islands he might discover , and also granted 10-?? of all profits of his voyage .",
            "Who was nicknamed The Little Corporal ?",
            "Who was president in 1913 ?",
            "Who was shot in the back during a Poker game in Deadwood , the Dakota territory ?",
            "Who was the 15th century fire-and-brimstone monk who gained control of Florence but ended burnt at the stake ?",
            "Who was the 16th President of the United States ?",
            "Who was the 1st U.S. President ?",
            "Who was the 23rd president of the United States ?",
            "Who was the 3rd president of the United States ?",
            "Who was the Charlie perfume woman ?",
            "Who was the Columbia Pictures head who forged actor Cliff Robertson 's name on a $1 , 000 check ?",
            "Who was the Democratic nominee in the American presidential election ?",
            "Who was the Russian ambassador to Hungary during the 1956 uprising ?",
            "Who was the Secretary of War in the Civil War during the Battle of Gettysburg ?",
            "Who was the abolitionist who led the raid on Harper 's Ferry in 1859 ?",
            "Who was the accused in The Trial of the Century , which opened Janurary 1 , 1935 ?",
            "Who was the actor who played Sam in the movie Casablanca ?",
            "Who was the architect of Central Park ?",
            "Who was the author of `` John Brown 's Body '' ?",
            "Who was the author of the book about computer hackers called `` The Cuckoo 's Egg : Tracking a Spy Through the Maze of Computer Espionage '' ?",
            "Who was the author of the famous fairy tale `` Snow White and Seven Dwarfs '' ?",
            "Who was the author of the novel `` Far From the Madding Crowd '' ?",
            "Who was the bandleader mentor of Ella Fitzgerald with whom she cowrote `` A_Tisket , A-Tasket '' ?",
            "Who was the captain of the tanker , Exxon Valdez , involved in the oil spill in Prince William Sound , Alaska , 1989 ?",
            "Who was the conservationist who served as spokesperson for Post Grape Nuts ?",
            "Who was the famous door-to-door brush salesman ?",
            "Who was the first African American to play for the Brooklyn Dodgers ?",
            "Who was the first African American to win the Nobel Prize in literature ?",
            "Who was the first American citizen awarded the Albert Medal of the Society of Arts ?",
            "Who was the first American in space ?",
            "Who was the first American poet to win the Nobel Prize for literature , in 1948 ?",
            "Who was the first American to walk in space ?",
            "Who was the first American world chess champion ?",
            "Who was the first English circumnavigator of the globe ?",
            "Who was the first Holy Roman Emperor ?",
            "Who was the first President to appoint a woman to head a cabinet ?",
            "Who was the first Prime Minister of Canada ?",
            "Who was the first Russian astronaut to walk in space ?",
            "Who was the first Taiwanese President ?",
            "Who was the first U.S. president to appear on TV ?",
            "Who was the first US President to ride in an automobile to his inauguration ?",
            "Who was the first X-Man to die in battle ?",
            "Who was the first actress to appear on a postage stamp ?",
            "Who was the first black golfer to tee off in the Masters ?",
            "Who was the first black performer to have his own network TV show ?",
            "Who was the first black to be head coach of a major league pro sports team ?",
            "Who was the first black woman to star in the Folies Bergeres ?",
            "Who was the first coach of the Cleveland Browns ?",
            "Who was the first doctor to successfully transplant a liver ?",
            "Who was the first elected mayor of Washington , D.C. ?",
            "Who was the first female United States Representative ?",
            "Who was the first governor of Alaska ?",
            "Who was the first governor of West Virginia ?",
            "Who was the first host of Person to Person ?",
            "Who was the first jockey to ride two Triple Crown winners ?",
            "Who was the first king of England ?",
            "Who was the first man to fly across the Pacific Ocean ?",
            "Who was the first man to return to space ?",
            "Who was the first person inducted into the U.S. Swimming Hall of Fame ?",
            "Who was the first person to reach the North Pole ?",
            "Who was the first person to study the stars ?",
            "Who was the first vice president of the U.S. ?",
            "Who was the first woman golfer to earn a million ?",
            "Who was the first woman governor in the U.S. ?",
            "Who was the first woman governor of Wyoming ?",
            "Who was the first woman in space ?",
            "Who was the first woman killed in the Vietnam War ?",
            "Who was the first woman to fly solo across the Atlantic ?",
            "Who was the first woman to run the mile in less than 4 36893 minutes ?",
            "Who was the founding member of the Pink Floyd band ?",
            "Who was the girl in Peter Sellers 's soup ?",
            "Who was the inventor of silly putty ?",
            "Who was the inventor of the stove ?",
            "Who was the king who signed the Magna Carta ?",
            "Who was the king who was forced to agree to the Magna Carta ?",
            "Who was the last U.S. president to reinstate Selective Service registration ?",
            "Who was the last woman executed in England ?",
            "Who was the lawyer for Randy Craft ?",
            "Who was the lawyer for Randy Steven Craft ?",
            "Who was the lawyer who represented Randy Steven Craft ?",
            "Who was the lead actress in the movie ` Sleepless in Seattle ' ?",
            "Who was the lyricist and who was the composer between Gilbert and Sullivan ?",
            "Who was the most famous food editor of The New York Times ?",
            "Who was the mother of the man who would not be king , the duke of Windsor ?",
            "Who was the oldest U.S. president ?",
            "Who was the only U.S. President to wear a Nazi uniform ?",
            "Who was the only person convicted in the My Lai Massacre ?",
            "Who was the only president to serve two nonconsecutive terms ?",
            "Who was the original Humpty Dumpty ?",
            "Who was the president of Vichy France ?",
            "Who was the prophet of the Jewish people ?",
            "Who was the prophet of the Muslim people ?",
            "Who was the second man to walk on the moon ?",
            "Who was the second person ever to wear Iron Man 's armor ?",
            "Who was the star of Leave It to Beaver ?",
            "Who was the star of the 1965 Broadway hit Golden Boy ?",
            "Who was the star witness at the Senate Watergate hearings ?",
            "Who was the supreme god of Germanic religion ?",
            "Who was the tallest U.S. president ?",
            "Who was with Patricia Hearst the night she was kidnaped ?",
            "Who were leaders of the Byzantine empire ?",
            "Who were the 1974 Oscar winners ?",
            "Who were the Picts ?",
            "Who were the `` filthiest people alive ? ''",
            "Who were the five Marx brothers ?",
            "Who were the four famous founders of United Artists ?",
            "Who were the head writers for the Smothers Brothers Comedy Hour ?",
            "Who were the only two bald U.S. Presidents ?",
            "Who won Ms. American in 1989 ?",
            "Who won Oscars for her roles in Gone with the Wind and A Streetcar Named Desire ?",
            "Who won World War II ?",
            "Who won a Pulitzer Prize for his novel The Caine Mutiny ?",
            "Who won the 1967 Academy Award for Best Actor ?",
            "Who won the 1968 California Democratic primary ?",
            "Who won the Battle of Gettysburg ?",
            "Who won the Nobel Peace Prize in 1991 ?",
            "Who won the Superbowl in ?",
            "Who won the first World Series ?",
            "Who won the first general election for President held in Malawi in May 1994 ?",
            "Who won the rugby world cup in ?",
            "Who won two gold medals in skiing in the Olympic Games in Calgary ?",
            "Who would you use the Heimlich maneuver on ?",
            "Who wrote : `` Poems are made by fools like me but only God can make a tree '' ?",
            "Who wrote Brave New World ?",
            "Who wrote NN DT NNP NNP '' ?",
            "Who wrote Sons and Lovers ?",
            "Who wrote The Collector ?",
            "Who wrote The Godfather ?",
            "Who wrote The Look of Love after viewing Ursula Andress ?",
            "Who wrote The Night of the Iguana ?",
            "Who wrote The Red Badge of Courage ?",
            "Who wrote The Secret Life of Walter Mitty ?",
            "Who wrote The Ugly Duckling ?",
            "Who wrote Unsafe at Any Speed ?",
            "Who wrote ` Dubliners ' ?",
            "Who wrote ` Hamlet ' ?",
            "Who wrote ` The Pines of Rome ' ?",
            "Who wrote `` Much Ado About Nothing '' ?",
            "Who wrote `` The Divine Comedy '' ?",
            "Who wrote `` The Pit and the Pendulum '' ?",
            "Who wrote `` The Scarlet Letter '' ?",
            "Who wrote the Bible ?",
            "Who wrote the Farmer 's Almanac ?",
            "Who wrote the bestselling Missionary Travels and Researches in South Africa , published in 1857 ?",
            "Who wrote the book , `` Huckleberry Finn '' ?",
            "Who wrote the book , `` Song of Solomon '' ?",
            "Who wrote the book , `` The Grinch Who Stole Christmas '' ?",
            "Who wrote the hymn `` Amazing Grace '' ?",
            "Who wrote the lyrics to Porgy and Bess ?",
            "Who wrote the poem that starts `` I love your lips when they 're wet with wine and red with a warm desire '' ?",
            "Who wrote the sci-fi trilogy Foundation , Foundation and Empire , and Second Foundation ?",
            "Who wrote the song , `` Silent Night '' ?",
            "Who wrote the song , `` Stardust '' ?",
            "Whom did Friz Freleng add to the Warner Bros. cartoon ranks ?",
            "Whom did Lauren Bacall marry after her husband Humphrey Bogart died ?",
            "Whom does Uncle Duke 's girl friend , Honey , room with ?",
            "Whose acceptance speech of more than 3 minutes prompted a time limit on Academy Award thank-yous ?",
            "Whose autobiography is titled Yes I Can ?",
            "Whose biography by Maurice Zolotow is titled Shooting Star ?",
            "Whose cover is that of an employee of Universal Import and Export ?",
            "Whose cupboard was bare ?",
            "Whose first presidential order was : `` Let 's get this goddamn thing airborne '' ?",
            "Whose funeral train traveled from Washington D.C. to Springfield , Illinois ?",
            "Whose husbands have included Conrad Hilton Jr. , and Michael Wilding ?",
            "Whose image is alleged to be on The Shroud of Turin ?",
            "Whose kidnaping was termed The Crime of the Century ?",
            "Whose old London come-on was : `` Buy my sweet lavender '' ?",
            "Whose singing voice was dubbed in for Natalie Wood in West Side Story and Audrey Hepburn in My Fair Lady ?",
            "Whose special bear 's creator was born on January 18 , 1779 ?",
            "Whose video is titled Shape Up with Arnold ?",
            "With whom did Bush compare Saddam Hussein ?"
        ]
        for q in test:
            self.assertIn(QuestionSubType.HUMAN_INDIVIDUAL,
                          predict_question_type(q))


class TestLocationQuestions(unittest.TestCase):
    def test_city(self):
        test = [
            "What city is also known as  ' The Gateway to the West ' ?",
            "What are the twin cities ?",
            "What city 's newspaper is called `` The Enquirer '' ?",
            "What city 's newspaper is called `` The Star '' ?",
            "What city had a world fair in 1900 ?",
            "what city has the zip code of 35824 ?",
            "What county is Modesto , California in ?",
            "What county is Phoenix , AZ in ?",
            "In what county is Eckley Colorado ?",
            "What county is Chicago in ?",
            "What is the capital of Ethiopia ?",
            "What is the capital of Mongolia ?",
            "What is the capital of Persia ?",
            "What is the capital of Yugoslavia ?",
            "What is the capital of Zimbabwe ?",
            "What is the largest city in the U.S. ?",
            "What is the largest city in the world ?",
            "What is the oldest city in the United States ?",
            # "Where is Milan ?",
            "In Sinclair Lewis ' `` Main Street , '' what was the name of the typical American town ?",
            "In what city does Maurizio Pellegrin now live ?",
            "In what city is the US Declaration of Independence located ?",
            "In what city is the famed St. Mark 's Square ?",
            "In what city is the headquarters of Sinn Fein ?",
            "McCarren Airport is located in what city ?",
            "Tell me what city the Kentucky Horse Park is near ?",
            "The Kentucky Horse Park is close to which American city ?",
            "The Kentucky Horse Park is located near what city ?",
            "The Orange Bowl is in what city ?",
            "The Orange Bowl is located in what city ?",
            "What 's the capital of Iowa ?",
            "What 's the capital of Monaco ?",
            "What 's the capital of Taiwan ?",
            "What 's the largest U.S. city on the Great Lakes ?",
            "What 's the oldest capital city in the Americas ?",
            "What African capital is named for a U.S. president ?",
            "What Asian city boasts the world 's biggest bowling alley ?",
            "What Australian city became the home of the America 's Cup ?",
            "What Colorado city owns its own glacier ?",
            "What European capital celebrated its 2 , 000th anniversary in 1951 ?",
            "What European city do Nicois live in ?",
            #  "What French seaport claims to be The Home of Wines ?",
            "What Georgia town did Scarlett O 'Hara condemn as being full of pushy people ?",
            "What German city do Italians call The Monaco of Bavaria ?",
            "What Italian city of 155 were Leonardo da Vinci , Michaelangelo , and Machiavelli all working in ?",
            "What Japanese city was once called Edo ?",
            "What Kentucky city calls itself The Horse Center of America ?",
            "What Kenyan city is the safari center for East Africa ?",
            "What Nevada center has been dubbed The Biggest Little City in the World ?",
            #   "What New Hampshire hamlet rises early to vote first in U.S. presidential elections ?",
            "What North American city boasts the biggest Polish population ?",
            "What North American city sprouts the most parking meters ?",
            "What North American city would you visit to see Cleopatra 's Needle ?",
            "What Peruvian city is home to the mummified body of Francisco Pizarro ?",
            "What Russian city boasts the Hermitage Museum ?",
            "What Russian city used to be called St. Petersburg and Petrograd ?",
            #    "What Russian seaport has a name meaning `` Lord of the East '' ?",
            "What Scandinavian capital is built on nine bridge-connected islands ?",
            "What South American capital is the world 's highest ?",
            "What South American city features the exclusive Copacabana Beach and Ipanema ?",
            "What South American city has the world 's highest commercial landing field ?",
            "What South Korean city is served by Kimpo International Airport ?",
            "What Southern California town is named after a character made famous by Edgar Rice Burroughs ?",
            "What Texas city got its name from the Spanish for `` yellow '' ?",
            "What U.S. city 's skyline boasts the Gateway Arch ?",
            "What U.S. city is The Queen of the Pacific ?",
            "What U.S. city is known as The Rubber Capital of the World ?",
            "What U.S. city was named for St. Francis of Assisi ?",
            "What United States city produces the most oil ?",
            "What are the 10 largest cities in the US ?",
            "What are the capital cities of the two large countries that occupy the Iberian peninsula in Europe ?",
            "What are the five most expensive cities in the world ?",
            "What are the ten safest American cities for pedestrians ?",
            "What are the two cities in Dicken 's `` A Tale of Two Cities '' ?",
            "What capital is built around Monument Circle which contains soldiers and sailors monument ?",
            "What city 's airport is named Logan International ?",
            "What city 's the kickoff point for climbs of Mount Everest ?",
            "What city 's theatrical district has been dubbed The Roaring Forties ?",
            "What city boasts Penn 's Landing , on the banks of the Delaware river ?",
            "What city boasts the Billingsgate fishmarket ?",
            "What city contains the district of Hell 's Kitchen ?",
            "What city did the Flintstones live in ?",
            "What city did the Mormons establish as their headquarters in 1847 ?",
            "What city does McCarren Airport serve ?",
            "What city does Orly Airport serve ?",
            "What city gained renown for its pea-soup fogs ?",
            "What city has a newspaper called The Plain Dealer ?",
            "What city has the two steepest streets in the U.S. ?",
            "What city has the world 's longest subway system ?",
            "What city hosted the first Winter Olympics in Asia ?",
            "What city houses the U.S. headquarters of Procter and Gamble ?",
            "What city in Florida is Sea World in ?",
            "What city in the U.S. experienced the most growth recently ?",
            "What city is . KDGE Radio located in ?",
            "What city is Logan Airport in ?",
            "What city is found in the city of OZ ?",
            "What city is graced by the Arch of Titus ?",
            "What city is near the mouth of the Amazon ?",
            "What city is often called The Insurance Capital of the World ?",
            "What city is served by Logan International Airport ?",
            "What city is served by McCarren Airport ?",
            "What city is served by Tempelhol Airport ?",
            "What city is sometimes called Gotham ?",
            "What city is sometimes called The Athens of Switzerland ?",
            "What city is terrorized by Dracula in The Night Stalker ?",
            "What city is the Kentucky Horse Park near ?",
            "What city is the setting for Puccini 's opera La Boheme ?",
            "What city is wiener schnitzel named for ?",
            "What city or state do the most gay men live in ?",
            "What city was Bobby Kennedy assassinated in ?",
            "What city was John F. Kennedy nominated for president in ?",
            "What city was Martin Luther King Jr. assassinated in ?",
            "What city was President William McKinley shot in ?",
            "What city would you be in if you were feeding the pigeons in the Piazza San Marco ?",
            "What is California 's capital ?",
            "What is one of the cities that the University of Minnesota is located in ?",
            "What is the capital of Burkina Faso ?",
            "What is the capital of California ?",
            "What is the capital of Congo ?",
            "What is the capital of Italy ?",
            "What is the capital of Kosovo ?",
            "What is the capital of Seattle ?",
            "What is the capital of Uruguay ?",
            "What is the city in which Maurizio Pellegrin lives called ?",
            "What is the largest city in Connecticut ?",
            "What is the largest city in Germany ?",
            "What is the largest city in Texas ?",
            "What is the largest city in the world ?",
            "What is the largest city on the Great Lakes ?",
            "What is the most populated city in the world ?",
            "What is the name of the city that Maurizio Pellegrin lives in ?",
            "What is the name of the largest city in Chile , South America ?",
            "What is the snowiest city in the U.S. ?",
            "What state capital comes last alphabetically ?",
            "What town was the setting for The Music Man ?",
            "What two Japanese cities are spelled with the letters K , O , O , T and Y ?",
            "What two cities usually mark the extremes of English Channel swims ?",
            "What was the first town to be chartered in Vermont ?",
            "What was the largest city in the world to declare martial law in 1989 ?",
            "What were the cities of Dickens 's A Tale of Two Cities ?",
            "What were the first three cities to have a population of more than a million ?",
            "Which city did Christian Crusaders fight to recapture from the Muslims ?",
            "Which city has the oldest relationship as a sister�city with Los Angeles ?",
            "Which city in Canada is the least-populated ?",
            "Which city in China has the largest number of foreign financial companies ?",
            "Which large U.S. city had the highest murder rate for 1988 ?"
        ]
        for q in test:
            self.assertIn(QuestionSubType.LOCATION_CITY,
                          predict_question_type(q))

    def test_state(self):
        test = [
            "In which state would you find the Catskill Mountains ?",
            "What French province is cognac produced in ?",
            "What U.S. state 's motto is `` Live free or Die '' ?",
            "What province is Montreal in ?",
            "What state did the Battle of Bighorn take place in ?",
            "What state has the least amount of rain per year ?",
            "What state is the geographic center of the lower 48 states ?",
            "In what U.S. state was the first woman governor elected ?",
            "In what state was the first co-educational college established",
            "In what state was there an 11 million gallon oil spill ?",
            "In which state are the Mark Twain National Forests ?",
            "Mississippi has what name for a state nickname ?",
            "What 's the northernmost U.S. state apart from Alaska ?",
            "What New England state carries the telephone area code 27 ?",
            "What New England state covers 5.9 square miles ?",
            "What U.S. state 's biggest lake is Lake Sam Rayburn ?",
            "What U.S. state are the Finger Lakes in ?",
            "What U.S. state boasts Leif Ericson Park ?",
            "What U.S. state boasts Stone Mountain , the world 's largest mass of exposed granite ?",
            "What U.S. state borders Illinois to the north ?",
            "What U.S. state comes last in an alphabetical list ?",
            "What U.S. state does the Continental Divide leave to enter Canada ?",
            "What U.S. state ends with a G ?",
            "What U.S. state has an element named for it ?",
            "What U.S. state has sagebrush as its state flower ?",
            "What U.S. state has the lowest highest elevation at 6 feet ?",
            "What U.S. state has the most blondes ?",
            "What U.S. state has the second-longest coastline ?",
            "What U.S. state includes the San Juan Islands ?",
            "What U.S. state is Dixville Notch in ?",
            "What U.S. state is Fort Knox in ?",
            "What U.S. state is Mammoth Cave National Park in ?",
            "What U.S. state lived under six flags ?",
            "What U.S. state records the least rainfall ?",
            "What are all the southern states of the U.S. ?",
            "What are all the southern states of the United States ?",
            "What are the only two states that incorporate the Confederate battle flag in their flags ?",
            "What eastern state sprouted the first commercial nuclear power plant in the U.S. ?",
            "What four U.S. states have active volcanoes ?",
            "What is the fastest growing state in the U.S.A. in 1998 ?",
            "What is the largest U.S. state east of the Mississippi ?",
            "What is the leading pecan and peanut growing state ?",
            "What is the nickname for the state of Mississippi ?",
            #    "What is the nickname of Pennsylvania ?",
            "What is the richest state in the U.S. ?",
            "What is the state nickname of Mississippi ?",
            "What populous state covers 49 , 576 square miles ?",
            "What province is Edmonton located in ?",
            "What southwestern state is dubbed The Silver State ?",
            "What sprawling U.S. state boasts the most airports ?",
            "What state 's home to the Buffalo Bill Historical Center ?",
            "What state did Anita Bryant represent in the 1959 Miss America contest ?",
            "What state did Helen Keller call home ?",
            "What state does Charles Robb represent ?",
            "What state does Martha Stewart live in ?",
            "What state full of milk and honey was the destination in The Grapes of Wrath ?",
            "What state has the longest Great Lakes shoreline ?",
            "What state has the most Indians ?",
            "What state in the U.S. has the most blacks ?",
            "What state in the United States covers the largest area ?",
            "What state is John F. Kennedy buried in ?",
            "What state is Mount McKinley in ?",
            "What state is Niagara Falls located in ?",
            "What state is known as the Hawkeye State ?",
            "What state is the Filenes store located in ?",
            "What state on the Gulf of Mexico has its lowest point five feet below sea level ?",
            "What state produces the best lobster to eat ?",
            "What state was Herbert Hoover born in ?",
            "What state was named the Green Mountain state ?",
            "What states do not have state income tax ?",
            "What two states is Washington D.C. between ?",
            "Which two states enclose Chesapeake Bay ?"
        ]
        for q in test:
            self.assertIn(QuestionSubType.LOCATION_STATE,
                          predict_question_type(q))

    def test_country(self):
        test = [
            "Which country gave New York the Statue of Liberty ?",
            "What country did Ponce de Leon come from ?",
            "Which country has the most water pollution ?",
            "Kosovo is a province of what country ?",
            "In what country is Lund ?",
            "In what country is a stuck-out tongue a friendly greeting ?",
            "In what nation is Edessa located nowadays ?",
            "Jackson Pollock is of what nationality ?",
            "Jackson Pollock was a native of what country ?",
            "Name a country that is developing a magnetic levitation railway system ?",
            "Name the country of giants twelve times the size of man in `` Gulliver 's Travels . ''",
            "Name the country which Honecker lived in .",
            "Name the largest country in South America .",
            "What 's the fifth-largest country in the world ?",
            "What 's the most powerful country in the world ?",
            "What 's the only East european country not tied to the ruble ?",
            "What African country is governed from Ouagadougou ?",
            "What African country was founded by freed American slaves in 1847 ?",
            "What Asian country has a bill of rights for cows ?",
            "What Asian country once thrilled to the sport of cricket fighting ?",
            "What European country 's monarchy was restored in 1975 ?",
            "What European country abandoned postage stamps in 1923 because printing them cost more than their face value ?",
            "What European country boasts the city of Furth , found where the rivers Rednitz and Pegnitz converge ?",
            "What European country is home to the beer-producing city of Budweis ?",
            "What Scandinavian country covers 173 , 732 square miles ?",
            "What South American country won its first World Cup soccer title in 1978 ?",
            "What are the Benelux countries ?",
            "What are the Nordic nations ?",
            "What are the five richest countries in the world ?",
            "What are the three most populated countries in the world ?",
            "What are the top five oil-producing countries in the world ?",
            "What bordering country is due north of Costa Rica ?",
            "What countries does the Mont Blanc Tunnel join ?",
            "What countries earn the most from tourism ?",
            "What countries have the best math students ?",
            "What countries have the highest ratio of university students ?",
            "What countries have the largest areas of forest ?",
            "What countries have the largest armed forces in the world ?",
            "What countries have the most auto thefts ?",
            "What country 's capital is Lagos ?",
            "What country 's capital is Tirana ?",
            "What country 's capital was formed when Pesth and Buda merged ?",
            "What country 's flag is field green ?",
            "What country 's national passenger rail system is called Via ?",
            "What country 's northernmost city is Darwin ?",
            "What country 's people are the top television watchers ?",
            "What country 's royal house is Bourbon-Parma ?",
            "What country , after Canada and Mexico , is closest to the U.S. ?",
            "What country and western singer is known as The Silver Fox ?",
            "What country are Godiva chocolates from ?",
            "What country are you in if you woo in the Wu dialect ?",
            "What country are you visiting if you land at President Duvalier Airport ?",
            "What country boasts Cawdor Castle , Glamis Castle , and Blair Castle ?",
            "What country boasts Ismail 's Palace and the Palace of King Farouk ?",
            "What country boasts the most cars per mile of road ?",
            "What country boasts the most dams ?",
            "What country boasts the southernmost point in continental Europe ?",
            "What country borders Denmark to the south ?",
            "What country borders the most others ?",
            "What country buys 25 percent of the world 's tea exports ?",
            "What country claimed Rubens , Van Dyck and Bruegel as citizens ?",
            "What country comes last in an alphabetical list ?",
            "What country contains Africa 's northernmost point ?",
            "What country contains the highest point in South America ?",
            "What country contains the westernmost point in South America ?",
            "What country covers 8 , 600 , 387 square miles ?",
            "What country did King Gustav V reign over from 197 to 195 ?",
            "What country did King Wenceslas rule ?",
            "What country did the Allies invade in World War II 's Operation Avalanche ?",
            "What country did the Mau Mau Uprising take place in ?",
            "What country did the Nazis occupy for 1 , CD NNS IN NNP NNP NNP .",
            "What country did the Nile River originate in ?",
            "What country did the Romans call Hibernia ?",
            "What country did the ancient Romans refer to as Hibernia ?",
            "What country do the Galapagos Islands belong to ?",
            "What country does Ileana Cotrubas come from ?",
            "What country has been called The Queen of the Antilles ?",
            "What country has declared one-fifth of its territory off-limits to Russians ?",
            "What country has problems with hooligans ?",
            "What country has the best defensive position in the board game Diplomacy ?",
            "What country has the highest arson rate ?",
            "What country has the highest per capita consumption of cheese ?",
            "What country has the largest sheep population ?",
            "What country has the most coastline ?",
            "What country has the most time zones , with 11 ?",
            "What country has the port of Haifa ?",
            "What country imposed the Berlin Blockade in 1948 ?",
            "What country in 1998 had the most suicides regardless of population size ?",
            "What country in Latin America is the largest one ?",
            "What country is Kosovo a part of ?",
            "What country is Mount Everest in ?",
            "What country is bounded in part by the Indian Ocean and Coral and Tasman seas ?",
            "What country is famous for Persian rugs ?",
            "What country is home to Heineken beer ?",
            "What country is located at 13 degrees North latitude and 10 degrees East longitude ?",
            "What country is proud to claim Volcano National Park ?",
            "What country is the biggest producer of tungsten ?",
            "What country is the largest diamond producer ?",
            "What country is the origin of the band the Creeps ?",
            "What country is the setting for Edgar Allan Poe 's The Pit and the Pendulum ?",
            "What country is the world 's largest importer of cognac ?",
            "What country is the worlds leading supplier of cannabis ?",
            "What country lies directly south of Detroit ?",
            "What country offered Albert Einstein its presidency in 1952 ?",
            "What country other than Germany invaded Poland in September 1939 ?",
            "What country owns Corsica ?",
            "What country received all the Nobel Prizes awarded in 1976 ?",
            "What country saw the origin of the Asian Flu ?",
            "What country surrounds San Marino , the world 's smallest Republic ?",
            "What country was A Terrible Beauty to Leon Uris ?",
            "What country was Brian Boru an 11th-century king of ?",
            "What country was Erich Honecker the leader of ?",
            "What country was General Douglas McArthur in when he was recalled by President Truman ?",
            "What country was Hitler the chancellor of ?",
            "What country was Kim Philby really working for ?",
            "What country was Mikhail Gorbachev the leader of ?",
            "What country was Sir Edmund Hillary born in ?",
            "What country was first to use the airplane as a weapon of war , against the Turks in Libya ?",
            "What country was the setting of You Only Live Twice ?",
            "What country will hit the year 2 first ?",
            "What country would you visit to ski in the Dolomites ?",
            "What desert country borders Saudi Arabia , Iraq and the Persian Gulf ?",
            "What is Stefan Edberg 's native country ?",
            "What is a country that starts with the letter x ?",
            "What is the country of origin for the name Thomas ?",
            "What is the most important nation in the world , historically ?",
            "What is the name of the country which Hitler ruled ?",
            "What is the smallest country in Africa ?",
            "What nation boarders Mozambique ?",
            "What nationality is Gorbachev ?",
            "What nationality is Ileana Cotrubas ?",
            "What nationality is Pope John Paul II ?",
            "What nationality is a Sicilian ?",
            "What nationality was Jackson Pollock ?",
            "What nationality were the 123 people who died in the Black Hole of Calcutta ?",
            "What southeast Asian country has the Wang River joining the Ping River at Tak ?",
            "What three European countries begin with the letter A ?",
            "What two Caribbean countries share the island of Hispaniola ?",
            "What two European countries are joined by the Gran San Bernardo Pass ?",
            "What two European countries entered the War of American Independence against the British ?",
            "What two South American countries do n't border Brazil ?",
            "What two countries ' coastlines border the Bay of Biscay ?",
            "What two countries are linked by the Brenner Pass ?",
            "What two countries are separated by the Bering Strait ?",
            "What two countries contain Sierra Nevada mountains ?",
            "What two countries fought the Hundred Years ' War ?",
            "What two countries in South America are landlocked ?",
            "What two countries is Andorra nestled between ?",
            "What two countries share the Khyber Pass ?",
            "What was the first country to put a second woman in space ?",
            "What was the nationality of Jackson Pollock ?",
            "What was the only country in the Western Hemisphere to join the Russian-led boycott of the 1984 Summer Olympics ?",
            "What was the only country you were allowed to drive into Israel from in 1979 ?",
            "Which Latin American country is the largest ?",
            "Which country did Hitler rule ?",
            "Which country is Australia 's largest export market ?",
            "Which country is known as `` Big Bear '' ?",
            "Which country is the largest country in Latin America ?",
            "Which is the wealthiest country in the world ?"
        ]
        for q in test:
            self.assertIn(QuestionSubType.LOCATION_COUNTRY,
                          predict_question_type(q))

    def test_mountain(self):
        test = [
            "What is the fourth highest mountain in the world ?",
            "Where are the Rocky Mountains ?",
            "Which mountain range in North America stretches from Maine to Georgia ?",
            "Name the highest mountain .",
            "What 's the second-highest mountain in the world ?",
            "What Rocky Mountain ridge separates North America 's eastward and westward-flowing rivers ?",
            "What are the four largest mountain ranges in the continental United States ?",
            "What are the four largest mountain ranges on the Asian continent ?",
            "What is New England 's highest mountain ?",
            "What is the highest mountain in the world ?",
            "What is the highest peak in Africa ?",
            "What is the name of the highest mountain in Africa ?",
            "What is the name of the tallest mountain in the world ?",
            "What is the second highest mountain peak in the world ?",
            "What is the tallest mountain ?",
            "What is the world 's highest peak ?",
            "What mountain range extends from the Gulf of St. Lawrence to Alabama ?",
            "What mountain range is traversed by the highest railroad in the world ?",
            "What mountain range marks the border of France and Spain ?",
            "What mountains lie between the Arkansas and Missouri rivers ?",
            "What was the highest mountain on earth before Mount Everest was discovered ?",
            "Where do people mountain climb in Nepal ?",
            "Where is the highest point in Japan ?"
        ]
        for q in test:
            self.assertIn(QuestionSubType.LOCATION_MOUNTAIN,
                          predict_question_type(q))

    def test_other(self):
        test = [
            "What river runs through Rowe , Italy ?",
            "In 139 the papal court was forced to move from Rome to where ?",
            "In Poland , where do most people live ?",
            "In the late 1700 's British convicts were used to populate which colony ?",
            "In what area of the world was the Six Day War fought ?",
            "In what part of Africa is Mozambique located ?",
            "In what part of the world is Mozambique ?",
            "Name a civil war battlefield .",
            "Name an art gallery in New York .",
            "On what avenue is the original Saks department store located ?",
            "On what continent is Mozambique ?",
            "On what river is Rome built ?",
            "On what river is Strasbourg built ?",
            "On which Hawaiian island is Pearl Harbor ?",
            # "What 's the closest G2 Spectrum Yellow Dwarf to Earth ?",
            # "What 's the farthest planet from the sun ?",
            # "What 's the home of the Rockettes ?",
            "What 's the largest island in the West Indies ?",
            "What 's the longest river in Canada ?",
            "What 's the longest river in the world ?",
            "What 's the most common street name in America ?",
            "What 's the name of a hotel in Indianapolis ?",
            "What 's the name of the Wilkes plantation in Gone with the Wind ?",
            "What 's the name of the temple that is located near the capital city of Laos ?",
            #   "What 's the nearest star to Earth ?",
            "What 's the sacred river of India ?",
            "What 's the second-largest island in the world ?",
            "What 's the tallest building in New York City ?",
            #   "What 's the world 's largest cathedral ?",
            "What 's the world 's longest suspension bridge ?",
            "What Asian gulf were the destroyers Maddox and C Turner Joy shot up in ?",
            "What California bay 's largest island is Angel Island ?",
            "What California bridge was Don Brown the first to cross , on May 27 , 1937 ?",
            "What California desert is dubbed High Desert ?",
            "What Caribbean island is northeast of Trinidad ?",
            "What Caribbean island is sometimes called Little England ?",
            # "What London museum features a Chamber of Horrors ?",
            "What London street claims to be the world center for men 's tailoring ?",
            "What London street is the home of British journalism ?",
            "What Mediterranean island is home to the first Club Med ?",
            "What Metropolis landmark was first introduced in the Superman cartoons of the 1940 's ?",
            "What New York City landmark has 168 steps to its crown ?",
            "What New York City structure is also known as the Twin Towers ?",
            "What Tokyo street glitters with famed department stores and nightclubs ?",
            #  "What airport is on the Piccadilly subway line ?",
            "What are Britain 's two longest rivers ?",
            "What are Canada 's two territories ?",
            "What are all the rivers in Europe ?",
            "What are some good fractal web sites ?",
            "What are some good medical sites for information ?",
            "What are some mythology websites ?",
            #  "What are the biggest Indian airports ?",
            #   "What are the largest breweries in the world ?",
            "What are the largest deserts in the world ?",
            #   "What are the largest libraries in the US ?",
            "What are the names of all the seas in the world and what ocean do they drain into ?",
            #    "What are the names of the tourist attractions in Reims ?",
            "What are the seven seas ?",
            "What are the top 5 tallest buildings in the world ?",
            "What are the world 's four oceans ?",
            "What are the world 's three largest oceans , in order of size ?",
            #   "What are tourist attractions in Reims ?",
            #   "What attracts tourists to Reims ?",
            #    "What bay divides Maryland 's Eastern and Western Shores ?",
            #    "What bay sparkles next to Miami , Florida ?",
            "What body of water are the Canary Islands in ?",
            "What body of water does the Danube River flow into ?",
            "What body of water does the Yukon River empty into ?",
            #     "What botanical marvel did Nebuchadnezzar build ?",
            "What building appropriately enough is depicted on the back of the 1-dollar bill ?",
            "What building are British monarchs crowned in ?",
            "What building built in 18 contains 327 miles of book shelves ?",
            #    "What canal does the Thatcher Ferry Bridge span ?",
            #    "What cathedral was Thomas Becket murdered in ?",
            #    "What celestial body has a diameter of 864 , 000 miles ?",
            "What colorful sea 's region does Greek legend say the Amazons lived near ?",
            #    "What constellation contains the twins Castor and Pollux ?",
            #    "What constellation is known as The Water Bearer ?",
            #    "What constellation represents a hunter with club and shield ?",
            "What continent 's name appears on the upper left corner of a Budweiser label ?",
            "What continent is Argentina on ?",
            "What continent is Bolivia on ?",
            "What continent is Egypt on ?",
            "What continent pushes up the Executive Committee mountain range ?",

            "What desert has been called The Garden of Allah ?",
            "What desert has the highest sand dunes ?",
            #   "What direction do most baseball pitchers pitch toward ?",
            #   "What direction do the best surfing beaches face ?",
            "What do most tourists visit in Reims ?",
            "What do we call the imaginary line along the top of the Rocky Mountains ?",
            "What does the River Seine empty into ?",
            "What erupts every hour at Yellowstone National Park ?",
            #  "What famed London criminal court was once a feudal castle ?",
            #  "What famed library can you reach by dialing 22-287-5 ?",
            "What famed river flows through Bagdad ?",
            "What famed river was Hernando de Soto the first European to see ?",
            "What famed strip of land is a 15-minute boat trip across the Venetian Lagoon from Venice ?",
            #  "What famed wall supports the Badaling turret ?",
            #  "What former royal palace has served as a granary , prison ,
            #  arsenal , leper colony , mint , telegraph station and whorehouse before becoming an art museum ?",
            #  "What gate opened on East and West Berlin ?",
            #  "What general direction does the journey in Around the World in 80 Days proceed in ?",
            "What hemisphere is the Philippines in ?",
            #   "What imaginary line is halfway between the North and South
            #   Poles ?",
            "What is Answers.com 's address ?",
            "What is Bill Gates of Microsoft E-mail address ?",
            "What is Bill Gross 's email address ?",
            "What is Britain 's possession on the Chinese mainland ?",
            "What is Drew Barrymore 's email address ?",
            "What is George Lucas 's e-mail address ?",
            "What is Mark McGwire 's e-mail address ?",
            "What is a reliable site that I can download Heretic 2 ?",
            #    "What is the Homelite Inc. home page ?",
            "What is the National Park in Utah ?",
            "What is the U.S. location of Procter & Gamble corporate offices ?",
            "What is the US Federal Government website for Standard Industrial Classification codes , SIC , ?",
            "What is the address for the main government office in Rome , Italy ?",
            "What is the address of the famous Mexican star `` Thalia '' ?",
            #  "What is the best hospital for orthopedics in the country ?",
            "What is the best online games site ?",
            "What is the best place to live in the world , considering climate , civilization ?",
            #   "What is the brightest star ?",
            #   "What is the brightest star visible from Earth ?",
            "What is the deepest area of the Arctic Ocean ?",
            "What is the deepest lake in the US ?",
            #    "What is the geographical center of the US including Alaska and Hawaii ?",
            "What is the greatest hiking Web site ?",
            #    "What is the habitat of the chickadee ?",
            "What is the highest continent ?",
            #    "What is the highest dam in the U.S. ?",
            #    "What is the highest waterfall in the United States ?",
            #    "What is the largest and most expensive freeway construction
            #    project in the U.S. right now ?",
            #    "What is the largest county in size in Massachusetts ?",
            "What is the largest island in the Mediterranean Sea ?",
            "What is the largest lake in North America ?",
            #  "What is the largest museum in the world ?",
            "What is the largest natural lake in Pennsylvania ?",
            #  "What is the largest office block in the world ?",
            #  "What is the largest shopping mall in the world ?",
            "What is the location of Edinburgh , Scotland ?",
            "What is the location of Lake Champlain ?",
            "What is the location of McCarren Airport ?",
            "What is the location of the Sea of Tranquility ?",
            "What is the longest place name in the U.S. ?",
            "What is the longest river in the United States ?",
            "What is the longest suspension bridge in the U.S. ?",
            "What is the most useful site on the Internet ?",
            #   "What is the name of the gulf between Sweden and Finland ?",
            #   "What is the name of the planet that the Ewoks live on ?",
            "What is the oldest building in the United States ?",
            #   "What is the oldest ethnological museum in the world ?",
            "What is the oldest website on the Internet ?",
            "What is the principal river of Ireland ?",
            "What is the rainiest place on Earth ?",
            #   "What is the seafaring name for the southern tip of South
            #   America ?",
            "What is the street address of the White House ?",
            "What is the tallest building in Japan ?",
            "What is the web address at which I can find the e-mail address of a member of the US House of Representatives ?",
            "What is the web address of the list of e-mail addresses of members of the House of Representatives ?",
            "What is the website for the USA journal ?",
            "What is website of the International Court of Justice ?",
            #  "What is worth seeing in Reims ?",
            "What island group contains Jersey , Guernsey , Sark and Herm ?",
            "What island group is Guadalcanal a part of ?",
            "What island has a park called The Battery at is southern tip ?",
            "What island is home to statues called Mauis ?",
            "What island was the target of the U.S. 's Operation Urgent Fury ?",
            "What islands got their name from the Spanish baja mar , meaning shallow water ?",
            "What kind of habitat does the scorpion live in ?",
            "What lake in Scotland is said to hold one or more monsters ?",
            "What lake is Sheboygan on ?",
            "What lake is the source of the White Nile ?",
            "What landmark Italian restaurant can be found at 239 West 48th Street , New York City ?",
            #    "What man-made waterways is 1.76 miles long ?",
            "What mountainous region of the world is the Lhasa Apso dog native to ?",
            #  "What natural attractions draw the most visitors in the United
            #  States ?",
            "What ocean did the Titanic sink in ?",
            "What ocean does Mauritania border ?",
            "What ocean is the largest in the world ?",
            "What ocean surrounds the Madeira Islands ?",
            "What ocean surrounds the Maldive Islands ?",
            "What ocean was Amelia Earhart flying over when she disappeared ?",
            "What park contains Firehole River and Fairy Falls ?",
            "What part of Britain comprises the Highlands , Central Lowlands , and Southern Uplands ?",
            "What peninsula is Spain part of ?",
            "What planet did Percival Lovell discover ?",
            "What planet gave bith to Superman ?",
            "What planet has the strongest magnetic field of all the planets ?",
            "What planet is known as the `` red '' planet ?",
            "What planet would you visit to see Bebrenia , Arcadia , and Amazonis ?",
            #   "What prison is found in Ossining , New York ?",
            "What river does the Grand Coulee Dam dam ?",
            "What river flows between Fargo , North Dakota and Moorhead , Minnesota ?",
            "What river flows past the Temple of Karnak ?",
            "What river flows through Vienna , Budapest and Belgrade ?",
            "What river in the US is known as the Big Muddy ?",
            "What river is Pocahontas buried along ?",
            "What river is Windsor Castle on ?",
            "What river runs through Colorado , Kansas , and Oklahoma ?",
            "What river runs through Liverpool ?",
            #   "What room did W.C. Fields keep his library in ?",
            "What sea did the Romans call mare nostrum ?",
            "What sea is Bombay on ?",
            "What sea separates Naples and Algiers ?",
            "What sea surrounds the Cayman Islands ?",
            #    "What sound does Olympia , Washington , overlook ?",
            "What soviet seaport is on the Black Sea ?",
            #   "What square is the geographical center of London ?",
            #   "What stadium do the Miami Dolphins play their home games in ?",
            "What strait links the Mediterranean Sea and the Atlantic Ocean ?",
            #   "What strait separates North America from Asia ?",
            "What sun-blasted , 14-mile wide valley is just north of the Mojave desert ?",
            #   "What volcano showers ash on Sicily ?",
            "What was Einstein 's birthplace ?",
            "What was known as the Spice Island ?",
            "What was the birthplace of Edgar Allen Poe ?",
            #  "What was the former residence of Scottish kings in Edinburgh ?",
            "What was the tallest building in America in 1922 ?",
            "What web sites are linked to the Report on Genesis Eldercare ?",
            "What were the first bodies visited by spacecraft ?",
            "When Superman needs to get away from it all , where does he go ?",
            "Where 's Montenegro ?",
            "Where 's the 19th hole on a golf course ?",
            "Where 's the Bernini-Bristol Hotel ?",
            "Where 's the GUM department store ?",
            "Where 's the Petrified Forest ?",
            "Where are 8 of the 10 highest mountains in the world ?",
            "Where are all European and American eels born ?",
            "Where are diamonds mined ?",
            "Where are good science sites on the Internet ?",
            "Where are some great educational resources for parents and teachers ?",
            "Where are the 49 steps ?",
            "Where are the Austerlitz and Victor Hugo subway stops ?",
            "Where are the British crown jewels kept ?",
            "Where are the Haversian canals ?",
            "Where are the National Archives ?",
            "Where are the U.S. headquarters for Procter & Gamble ?",
            "Where are the Union Stockyards ?",
            "Where are the apartments in Saint John , New Brunswick ?",
            "Where are the busiest Amtrak rail stations in the U.S. ?",
            "Where are the busiest ports in the world ?",
            "Where are the headquarters of Eli Lilly ?",
            "Where are the leading medical groups specializing in lung diseases ?",
            "Where are the tropical rain forest distributions ?",
            "Where are there aborigines ?",
            "Where are zebras most likely found ?",
            "Where can I buy a good snowboard for less than $200 ?",
            "Where can I buy a hat like the kind Jay Kay from Jamiroquai wears ?",
            "Where can I buy a pony on the Big Island for my daughter ?",
            "Where can I buy movies on videotape online ?",
            "Where can I find a `` Fifth Element '' screensaver ?",
            "Where can I find a case on Americans with Disabilities Act of 199 ?",
            "Where can I find a case on Individuals with Disabilities Education Act of 1991 ?",
            "Where can I find a large list of 5 to 6 letter words ?",
            "Where can I find a lesson plan for teaching the metric system conversion to American standard ?",
            "Where can I find a list of `` classic '' books 5th and 6th graders should read ?",
            "Where can I find a list of all the companies in America that offer a direct stock purchase plan ?",
            "Where can I find a person 's address from a telephone number ?",
            "Where can I find a picture of a Blue Meanie ?",
            "Where can I find a review of Nightmare on Elm Street in a film journal ?",
            "Where can I find a tape or book to help me say , write and understand Japanese ?",
            "Where can I find a website that gives comparisons of good prices ?",
            "Where can I find a world atlas map online at no charge ?",
            "Where can I find all the information I need to know about the English Civil War , 1642-1649 , ?",
            "Where can I find an Ask An Expert site ?",
            "Where can I find book reviews of `` Turbulent Souls '' ?",
            "Where can I find correct tabs for Third Eye Blind songs ?",
            "Where can I find detailed information about Manchukuo ?",
            "Where can I find examples of legal cases about the Individuals with Disabilities Education Act ?",
            "Where can I find free piano scores for popular music ?",
            "Where can I find full written draft of CTBT ?",
            "Where can I find info on Alexander Mackenzie ?",
            "Where can I find info on research being done on oilseeds thru genetics ?",
            "Where can I find information about Bob Barr , representative from Georgia ?",
            "Where can I find information about touring the Philippines ?",
            "Where can I find information on George Bush ?",
            "Where can I find information on becoming a journalist ?",
            "Where can I find information on the Narragansett Indians and other tribes in Rhode Island ?",
            "Where can I find information on the cyclone that hit New Jersey on 8/28/1941 ?",
            "Where can I find lyrics for R&B ?",
            "Where can I find out the top 1 singles ?",
            "Where can I find pictorial directions on how to build a very simple treehouse ?",
            "Where can I find scientific data , `` research papers , '' on textile engineering ?",
            "Where can I find the best free evidence for debate about Russia ?",
            "Where can I find the history of the Hungarian language ?",
            "Where can I find the history of the Taiwanese language ?",
            "Where can I find the lyrics for the song ` Getting Married Today ' from the musical ` Company ' ?",
            "Where can I find the names of all the 15 Pokemon ?",
            "Where can I find the schematics to the windshield wiper mechanism ?",
            "Where can I find the status of my tax return ?",
            "Where can I find up-to-date coastal ocean surface temperature information , preferably along North America and the Caribbean ?",
            "Where can I get U.S. economic statistics ?",
            "Where can I get a complete listing of showtimes in my area ?",
            "Where can I get a map of Prussia on the Internet ?",
            "Where can I get a photograph of professor Randolph Quirk ?",
            "Where can I get cotton textiles importer details ?",
            "Where can I get information about cystic fibrosis ?",
            "Where can I get information and statistics on countries and nations ?",
            "Where can I get information concerning child custody files for the State of Utah ?",
            "Where can I get information on the original 13 US colonies ?",
            "Where can I get mailing lists ?",
            "Where can I get piano music for the Jamiroquai song Everyday for the midi ?",
            "Where can I learn about Samuel Gompers ?",
            "Where can I look at a perpetual calendar ?",
            "Where can I read about Abraham Lincoln ?",
            "Where can I read about Chiang Kai-shek ?",
            "Where can I take a test that will tell me what I should be when I grow up ?",
            "Where can an individual get a contact lens tested that burned the entire surface of eye when new ?",
            "Where can one find Mozambique ?",
            "Where can one find Rider College ?",
            "Where can one find information on religion and health , the brain and nutrition ?",
            "Where can stocks be traded on-line ?",
            "Where can you find the Venus flytrap ?",
            "Where could I go to take a ride on a steam locomotive ?",
            "Where did Bill Gates go to college ?",
            "Where did Dikembe Mutombo go to college ?",
            "Where did Dylan Thomas die ?",
            "Where did Freidreich Wilhelm Ludwig Leichhardt , Prussian born explorer , go to school ?",
            "Where did George of the Jungle live ?",
            "Where did Gulliver find a race of tiny people ?",
            "Where did Hillary Clinton graduate college ?",
            "Where did Honecker rule ?",
            "Where did Howard Hughes die ?",
            "Where did King Francis I hang the `` Mona Lisa '' when he owned it ?",
            "Where did Luther display his `` Ninety-Five Theses '' ?",
            "Where did Sarge Steel get his metal hand ?",
            "Where did Ty Cobb grow up ?",
            "Where did Victor Hugo spend his exile ?",
            "Where did Wile E. Coyote always get his devices ?",
            "Where did Woodstock take place ?",
            "Where did bocci originate ?",
            "Where did cable cars first roll down Clay Street in 1873 ?",
            "Where did guinea pigs originate ?",
            "Where did he get the title ?",
            "Where did makeup originate ?",
            "Where did surfing originate ?",
            "Where did the 6th annual meeting of Indonesia-Malaysia forest experts take place ?",
            "Where did the Battle of the Bulge take place ?",
            "Where did the Inuits live ?",
            "Where did the Japanese Imperial Forces surrender to end WWII ?",
            "Where did the Maya people live ?",
            "Where did the Mayan Indians live ?",
            "Where did the Wright brothers make their first flight ?",
            "Where did the myth of Santa Claus originate ?",
            "Where did the name Daniel originate ?",
            "Where did the real St. Nicholas live ?",
            "Where did the sport of caber-tossing originate ?",
            "Where did the ukulele originate ?",
            "Where did the world come from ?",
            "Where do I find information for foreclosure properties on the Internet ?",
            "Where do apple snails live ?",
            "Where do hyenas live ?",
            "Where do lobsters like to live ?",
            "Where do quality drinks begin ?",
            "Where do the Blackhawks maintain their operations ?",
            "Where do the Grimace and Mayor McCheese live ?",
            "Where do the adventures of `` The Swiss Family Robinson '' take place ?",
            "Where do you find information about the Queensland National Competition Policy",
            "Where do you find the answers for all these questions ?",
            "Where does Barney Rubble go to work after he drops Fred off in the `` Flintstones '' cartoon series ?",
            "Where does Buzz Aldrin want to build a permanent , manned space station ?",
            "Where does Mother Angelica live ?",
            "Where does Ray Bradbury 's Chronicles take place ?",
            "Where does chocolate come from ?",
            "Where does dew come from ?",
            "Where does most of the marijuana entering the United States come from ?",
            "Where does the Santa Fe Trail begin and end ?",
            "Where does the U.S. get most of its energy ?",
            "Where does the opera singer Ileana Cotrubas come from ?",
            "Where does the song Anything Goes take place ?",
            "Where does the tennis star Stefan Edberg come from ?",
            "Where does the weird shape of the dinner fish knife originate from ?",
            "Where does tuberculosis come from ?",
            "Where have the most dinosaur remains been found ?",
            "Where in a tree does photosynthesis occur ?",
            "Where in the Americas is it only 47 miles from the Atlantic to the Pacific ?",
            "Where in the Bible does it tell about Jesus Christ 's brothers and sisters ?",
            "Where in the United States do people live the longest ?",
            "Where is Amsterdam ?",
            "Where is Ayer 's rock ?",
            "Where is Basque country located ?",
            "Where is Belize located ?",
            "Where is Burma ?",
            "Where is Dartmouth College ?",
            "Where is Erykah Badu originally from ?",
            "Where is Glasgow ?",
            "Where is Guam ?",
            "Where is Hearst Castle , built by publisher William Randolph Hearst ?",
            "Where is Hitler buried ?",
            "Where is Inoco based ?",
            "Where is John Wayne airport ?",
            "Where is Kings Canyon ?",
            "Where is Logan Airport ?",
            "Where is Los Vegas ?",
            "Where is McCarren Airport ?",
            "Where is McCarren Airport located ?",
            "Where is Melbourne ?",
            "Where is Microsoft 's corporate headquarters located ?",
            "Where is Mile High Stadium ?",
            "Where is Mozambique located ?",
            "Where is Natchitoches , Louisiana ?",
            "Where is Natick ?",
            "Where is Ocho Rios ?",
            "Where is Perth ?",
            "Where is Poe 's birthplace ?",
            "Where is Prince Edward Island ?",
            "Where is Procter & Gamble based in the U.S. ?",
            "Where is Procter & Gamble headquartered in the U.S. ?",
            "Where is Qatar ?",
            "Where is Rider College ?",
            "Where is Rider College located ?",
            "Where is Romania located ?",
            "Where is Santa Lucia ?",
            "Where is Sinn Fein 's headquarters ?",
            "Where is South Bend ?",
            "Where is Tornado Alley ?",
            "Where is Trinidad ?",
            "Where is Tufts University ?",
            "Where is Webster University ?",
            "Where is Windsor Castle ?",
            "Where is `` Global Schoolhouse '' ?",
            "Where is former Pro wrestler Johnny `` Rubber Man '' Walker ?",
            "Where is it planned to berth the merchant ship , Lane Victory , which Merchant Marine veterans are converting into a floating museum ?",
            "Where is one 's corpus callosum found ?",
            "Where is the Abominable Snowman said to wander ?",
            "Where is the Bulls basketball team based ?",
            "Where is the Danube ?",
            "Where is the Eiffel Tower ?",
            "Where is the Euphrates River ?",
            "Where is the Grand Canyon ?",
            "Where is the Henry Ford Museum ?",
            "Where is the Holland Tunnel ?",
            "Where is the Isle of Man ?",
            "Where is the Kalahari desert ?",
            "Where is the Keck telescope ?",
            "Where is the Kentucky Horse Park ?",
            "Where is the Kentucky Horse Park located ?",
            "Where is the Little League Museum ?",
            "Where is the Loop ?",
            "Where is the Lourve ?",
            "Where is the Mall of the America ?",
            "Where is the Mason/Dixon line ?",
            "Where is the Mayo Clinic ?",
            "Where is the Orange Bowl ?",
            "Where is the Orinoco ?",
            "Where is the Orinoco River ?",
            "Where is the Rose Bowl played ?",
            "Where is the Savannah River ?",
            "Where is the Shawnee National Forest ?",
            "Where is the Smithsonian Institute located ?",
            "Where is the Statistical Abstract of the United States online ?",
            "Where is the Taj Mahal ?",
            "Where is the Thomas Edison Museum ?",
            "Where is the Valley of the Kings ?",
            "Where is the Virtual Desk Reference ?",
            "Where is the actress , Marion Davies , buried ?",
            "Where is the biggest bell ?",
            "Where is the bridge over the river Kwai ?",
            "Where is the group M People from ?",
            "Where is the largest dam in the world ?",
            "Where is the largest post office building in the world ?",
            "Where is the location of the Orange Bowl ?",
            "Where is the massive North Korean nuclear complex located ?",
            "Where is the official `` zero '' of the sea level ?",
            "Where is the oldest living thing on earth ?",
            "Where is the tallest roller coaster located ?",
            "Where is the volcano Mauna Loa ?",
            "Where is the volcano Olympus Mons located ?",
            "Where is the world 's most active volcano located ?",
            "Where is the world championship sled dog race held each February ?",
            "Where is there information on the novel `` El Cid '' ?",
            "Where is your corpus callosum ?",
            "Where must a soccer goalie stand to be permitted to handle the ball ?",
            "Where on the Internet can I find a song lyrics database similar to the International Lyrics Server ?",
            "Where on the Internet can I find information on laundry detergent ?",
            "Where on the Internet can I get chemicals importers ?",
            "Where on the Internet can I get information about the Fifth Amendment on the American Bill of Rights ?",
            "Where on the Web is Adventours Tours from Sydney , Australia ?",
            "Where on the body is a mortarboard worn ?",
            "Where was Christopher Columbus born ?",
            "Where was George Washington born ?",
            "Where was Lincoln assassinated ?",
            "Where was Poe born ?",
            "Where was Pythagoras born ?",
            "Where was Richard Nixon when Gerald Ford became president ?",
            "Where was Tesla born ?",
            "Where was `` I have fallen , and I can 't get up '' said first ?",
            "Where was chop suey invented ?",
            "Where was helium first discovered , hence its name ?",
            "Where was the Cisalpine Republic , 1797-185 , ?",
            "Where was the Ligurian Republic , 1797-185 , ?",
            "Where was the first golf course in the United States ?",
            "Where was the first restaurant ?",
            "Where was the first zoo in the U.S. ?",
            "Where was the largest concentration camp in World War II ?",
            "Where were the 1936 Summer Olympics held ?",
            "Where were the 196 Summer Olympics held ?",
            "Which area produces the least acidic coffee ?",
            "Which continent has the most roses ?",
            "Which one of the Great Lakes is entirely within U.S. territory ?",
            "Which way do you turn your Bic to increase the flame - clockwise or counterclockwise ?",
        ]
        for q in test:
            self.assertIn(QuestionSubType.LOCATION_OTHER,
                          predict_question_type(q))


class TestNumericQuestions(unittest.TestCase):
    def test_numeric_others(self):
        test = [
            "10+4",
            "987-12",
            "what is 9837 times 345",
            "what is 573987 * 125326",
            "What does 7847+5943 equal ?",

            "What is the melting point of gold ?",
            "What is the melting point of copper ?",
            "How often does Old Faithful erupt at Yellowstone National Park ?",
            "How loud is thunder ?",

            "What 's a perfect score in a gymnastics exercise ?",

            "What 's the score of a forfeited baseball game ?",
            "What amount of folic acid should an expectant mother take daily ?",
            "What are the numbers that fit into Fermont 's last theorem ?",
            "What are the shoe sizes of O 'Neal , Jordan , and Mutombo , the NBA players ?",
            "What are the statistics for drunken drivers in Maryland ?",
            "What are the unemployment statistics for the years 1965 and 1990 ?",
            "What brand number graces the black label of a bottle of Jack Daniel 's ?",

            "What is the all-time stock high of Apple Computer , and where can I find this information ?",

            "What is the average hourly rate of American workers ?",
            "What is the chemical reactivity of argon ?",
            "What is the chemical reactivity of helium ?",
            "What is the chemical reactivity of neon ?",
            "What is the chromosome number of an elephant ?",
            "What is the frequency of VHF ?",
            "What is the horsepower of the shuttle boosters ?",
            "What is the latitude and longitude of El Paso , Texas ?",
            "What is the normal resting heart rate of a healthy adult ?",
            "What is the number of American soldiers deployed to South Korea ?",

            "What is the quantity of American soldiers still unaccounted for from the Vietnam war ?",

            "What number is at 12 o 'clock on a dartboard ?",
            "What number of American soldiers remain unaccounted from the Vietnam war ?",
            "What was Einstein 's IQ ?",
            "What was the number of people that Randy Steven Craft was convicted of killing ?",

            "How often are quadruplets born ?",  # count
        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_OTHER,
                          predict_question_type(q))

    def test_numeric_distance(self):
        test = [
            "How far away is the moon ?",
            "How far is Pluto from the sun ?",
            "How far is a nautical mile ?",
            "How far is it from Denver to Aspen ?",
            "How far is the service line from the net in tennis ?",
            "How long is the Columbia River in miles ?",
            "How tall is the Gateway Arch in St. Louis , MO ?",
            "How tall is the Sears Building ?",
            "How wide is the Milky Way galaxy ?",
            "What is the depth of the Nile river ?",
            "What is the diameter of a golf ball ?",
            "What 's the maximum length , in inches , of a first baseman 's glove ?",
            "What is the distance in miles from the earth to the sun ?",
            "What is the earth 's diameter ?",
            "What is the elevation of St. Louis , MO ?",
            "What is the length of the coastline of the state of Alaska ?",
            "What is the width of a football field ?",
            "How deep is a fathom ?",
            "How far away is the moon ?",
            "How far can a human eye see ?",
            "How far can a man travel in outer space ?",
            "How far can you see ?",
            "How far do you have to run if you hit a home run ?",
            "How far is London UK from California ?",
            "How far is Yaroslavl from Moscow ?",
            "How far is it from Phoenix to Blythe ?",
            "How far is the longest hole in 1 on any golf course and where did it happen ?",
            "How far out is the universe ?",
            "How high is the city of Denver ?",
            "How high must a mountain be to be called a mountain ?",
            "How long is Camptown Racetrack ?",
            "How long is the Coney Island boardwalk ?",

            "How long is the world 's largest ship , in meters ?",

            "How long were Tyrannosaurus Rex 's teeth ?",
            "How tall is Prince Charles ?",
            "How tall is kilamanjaro ?",
            "How tall is the Matterhorn ?",
            "How tall is the giraffe ?",
            "How tall is the replica of the Matterhorn at Disneyland ?",
            "How tall was the animated Frankenstein",
            "How tall was the animated King Kong ?",
            "How wide is the Atlantic Ocean ?",
            "What are the dimensions of an ice hockey goal ?",
            "What are the lengths of pearl necklaces ?",
            "What is the length of border between the Ukraine and Russia ?",
            "What is the wingspan of a condor ?",
            "What is the world record for the longest hair ?",

            # how long -> time period
            "How long was Mao 's 1930s Long March ?",
            "How long is the border between Canada and the 48 conterminous states ?",
        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_DISTANCE,
                          predict_question_type(q))

    def test_numeric_weight(self):
        test = [
            "What is the average weight of a Yellow Labrador ?",
            "What is the atomic weight of silver ?",
            'What does a teaspoon of matter weigh in a black hole ?',
            'What is the approximate weight of a teaspoon of matter in a black hole ?',
            'What is the average weight for a man ?',
            'What is the recommended weight of a 15 year-old male that is 5 , 6 ?',
            'What is the weight of a teaspoon of matter in a black hole ?',
            'What is the weight of air ?',
            # count
            'How many pounds are there in a stone ?',
            # count / money
            "How much did a knight 's armor weigh ?",
            'How much does a poodle weigh ?',
            "How much does water weigh ?",
            "How much does the human adult female brain weigh ?",
            'Approximately how much does a teaspoon of matter weigh in a black hole ?',

            # technically incorrect, the answer is not numeric
            'What do Englishmen weigh themselves in ?',

        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_WEIGHT,
                          predict_question_type(q))

    def test_numeric_temp(self):
        test = [
            "How cold should a refrigerator be ?",
            "The sun 's core , what is the temperature ?",
            "What is the average body temperature ?",
            "What is the temperature at the center of the earth ?",
            "What is the temperature of the sun 's surface ?",
            'How hot does the inside of an active volcano get ?',
            'How hot should the oven be when baking Peachy Oat Muffins ?',
            'How hot should the oven be when making Peachy Oat Muffins ?',
            "What 's the Fahrenheit equivalent of zero degrees centigrade ?",
            'What is the temperature for baking Peachy Oat Muffins ?',
            'What is the temperature for cooking ?',
            'What is the temperature today ?',
            'What should the temperature be set at while baking Peachy Oat Muffins ?'

        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_TEMPERATURE,
                          predict_question_type(q))

    def test_numeric_speed(self):
        test = [
            "How fast is alcohol absorbed ?",
            "How fast is sound ?",
            "How fast is the speed of light ?",
            "What is the average speed of the horses at the Kentucky Derby ?",
            "What is the speed hummingbirds fly ?",
            "What is the speed of light ?",
            'How fast can a Corvette go ?',
            'How fast do cheetahs run ?',
            'How fast does the fastest car go ?',
            'How fast is a 45Mhz processor ?',
            'How fast is light ?',
            "How fast must a spacecraft travel to escape Earth 's gravity ?",
            'What is the speed of the Mississippi River ?'
        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_SPEED,
                          predict_question_type(q))

    def test_numeric_age(self):
        test = [
            "What is the life expectancy of a dollar bill ?",
            "What is the life expectancy for crickets ?",
            "How long did Rip Van Winkle sleep ?",
            "How old do you have to be in order to rent a car in Italy ?",
            "How old was Elvis Presley when he died ?",
            "How old was Joan of Arc when she died ?",
            "How old was the youngest president of the United States ?",
            "What is the average life span for a chicken ?",
            "What is the gestation period for a cat ?",
            'At what age did Rossini stop writing opera ?',
            'How long after intercourse does it take to find out if you are pregnant ?',
            'How long ago did the Anglican church part from the Vatican ?',
            'How long ago was the Roe vs. Wade decision by the Supreme Court ?',
            'How long did Shea and Gould practice law in Los Angeles ?',
            'How long did it take Stanley to find Livingstone ?',
            'How long did the Charles Manson murder trial last ?',
            'How long did the Paris Commune hold out for against the rest of France ?',
            'How long do cardinal eggs incubate ?',
            'How long do flies live ?',
            'How long do hermit crabs live ?',
            'How long do you have to live in a community to vote ?',
            'How long do you have to pay back debt after claiming chapter 11 bankruptcy ?',
            'How long does James Bond like his eggs boiled ?',
            'How long does a dog sleep ?',
            'How long does a fly live ?',
            'How long does a human live ?',
            "How long does a pig 's orgasm last ?",
            'How long does cocaine stay in your system ?',
            'How long does it take different materials to decompose ?',
            "How long does it take for Spider-Man 's web to evaporate ?",
            'How long does it take for your blood to make one complete trip through the body ?',
            'How long does it take for your blood to make one complete trip through the body ?',
            'How long does it take for your body to restore blood after you donate your blood ?',
            'How long does it take light to reach the Earth from the Sun ?',
            'How long does it take sunlight to reach Earth ?',
            'How long does it take the Milky Way Galaxy to make one revolution ?',
            'How long does it take the moon to revolve around the Earth ?',
            'How long does it take the typical American to eat 23 quarts of ice cream ?',
            'How long does it take the typical hen to lay 19 dozen eggs ?',
            'How long does it take to hike the entire Appalachian Trail ?',
            'How long does it take to travel from Tokyo to Niigata ?',
            'How long does the average domesticated ferret live ?',
            'How long has L.L. Cool J. been married ?',
            'How long should a person wash their hands before they are clean ?',
            'How long should you feed your puppy Purina Puppy Chow ?',

            'How long would it take for a $ savings bond to mature ?',
            'How long would it take to get from Earth to Mars ?',
            'How old is Benny Carter ?',
            'How old is Bernadette Peters ?',
            'How old is Britney Spears ?',
            'How old is Jeremy Piven ?',
            'How old is Stevie Wonder ?',
            'How old is singer Freedy Johnston ?',
            'How old is the Italian artist Maurizio Pellegrin ?',
            'How old is the sun ?',
            'How old is the universe ?',
            'How old is too old for a child to not be talking ?',
            'How old was Gene Siskel ?',
            'How old was George Washington when he died ?',
            "How old was Lucille Ball when the show `` I Love Lucy '' premiered ?",
            'How old was Sir Edmund Hillary when he climbed Mt. Everest ?',
            'How old was Stevie Wonder when he signed with Motown Records ?',
            'On average , how long time does it take to type a screenplay ?',
            'Shea and Gould had an office in Los Angeles for how long before closing it ?',
            'The italian artist , Maurizio Pellegrin , is how old ?',
            'What age is Benny Carter ?',
            "What is Maurizio Pellegrin 's age ?",
            'What is the average age a horse lives ?',
            'What is the average age of a member of the team that worked on the Manhatten Project ?',
            'What is the average life expectancy of a male in Ireland in 1996 ?',
            'What is the average time it takes for a male to ejaculate ?',
            'What is the average time to kiss somene ?',
            'What is the gestation period for human pregnancies ?',
            'What is the life expectancy of an elephant ?',
            'What is the life span of the average monkey ?',
            'What is the recomended age to switch a child from a crib to a bed ?',
            'What is the time it takes a typist to type a screenplay that is 100 pages long ?',
            'What is the youngest age a boy or girl can have an orgasm ?',
            'What was the average life expectancy during the Stone Age ?',

            # how long is/was -> distance
            "For how long is an elephant pregnant ?",
            'How long is human gestation ?',
            "How long was the OJ Simpson trial ?",
            "How long was the TV mission of Star Trek 's Enterprise to be ?",
            'How long was the longest hiccup attack ?',
            'How long was the longest sneezing attack ?',
        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_PERIOD,
                          predict_question_type(q))

    def test_numeric_percent(self):
        test = [
            "Developing nations comprise what percentage of the world 's population ?",
            "What is the murder rate in Windsor , Ontario ?",
            "What is the protection rate of using condoms ?",
            "Independent silversmith 's account for what percentage of silver production ?",
            "Of children between the ages of two and eleven , what percentage watch `` The Simpsons '' ?",
            "What are the chances of pregnacy if the penis does not penetrate the vagina ?",
            "What are the chances of pregnacy if the penis does not penetrate the vagina ?",
            "What are the highest-paying odds on a roulette table ?",
            "What are the odds of giving birth to twins ?",
            "What fraction of a beaver 's life is spent swimming ?",
            "What is the chance of conceiving quadruplets ?",
            "What is the current unemployment rate in the U.S. ?",
            "What percent liked Thatcher after she had been in power for a decade ?",
            "What percent of world 's fresh water is found in Canada ?",
            "What percentage of American men are alcoholic ?",
            "What percentage of Americans own their homes ?",
            "What percentage of all world tornados touch down in the US ?",
            "What percentage of children between the ages of two and eleven watch ` The Simpsons ' ?",
            "What percentage of the body is muscle ?",
            "What percentage of the silver production is done by independent silversmiths ?",
            "What ratio of children of ages between two and eleven watch ` The Simpsons ' ?",
            "What was the target rate for M3 growth in 1992 ?",

            # money
            "What is the Pennsylvania state income tax rate ?",

            "What was Thatcher 's approval rating after 10 years in power ?",
            "What is the probability that at least 2 out of 25 people will have the same birthday ?",
            "What 's the percentage of children aged two through eleven who watch 'The Simpsons ' ?",
            "What percentage of the world 's plant and animal species can be found in the Amazon forests ?",
        ]

        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_PERCENTAGE,
                          predict_question_type(q))

    def test_numeric_volume(self):
        test = [
            'How big is Australia ?',
            'How big is a baby bald eagle ?',
            'How big is a normal size penis for a 15-year-old ?',
            'How big is a quart ?',
            'How big is our galaxy in diameter ?',
            'How big is the Chappellet vineyard ?',
            'How big is the Electoral College ?',
            'How big is the largest diamond ?',
            'How big is the universe actually ?',
            'How large is the Arctic refuge to preserve unique wildlife and wilderness '
            "value on Alaska 's north coast ?",
            'What is the acreage of the Chappellet vineyard ?',
            'What is the size of Argentina ?',
            'What is the size of the largest akita ?',
            "what is the volume of the observable universe"
        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_VOLSIZE,
                          predict_question_type(q))

    def test_numeric_ord(self):
        test = [
            "What chapter of Gone with the Wind has Rhett Butler leaving Scarlett O 'Hara ?",
            "What chapter of the Bible has the most verses ?",
            "in the bible, What chapter has the most verses ?",
            "Where does the U.S. rank among world countries in area ?"
        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_ORDINAL,
                          predict_question_type(q))

    def test_numeric_date(self):
        test = [
            "What year did the Titanic start on its journey ?",
            "Mercury , what year was it discovered ?",
            "What was the last year that the Chicago Cubs won the World Series ?",
            "What year did Canada join the United Nations ?",
            "What year did Mussolini seize power in Italy ?",
            "What year did Oklahoma become a state ?",
            "What year did WWII begin ?",
            "What year did the Andy Griffith show begin ?",
            "What year did the Milwaukee Braves become the Atlanta Braves ?",
            "What year did the NFL go on strike ?",
            "What year did the Titanic sink ?",
            "What year did the U.S. buy Alaska ?",
            "What year did the United States abolish the draft ?",
            "What year was Mozart born ?",
            "What year was the Mona Lisa painted ?",
            "In what year did China and the Republic of Korea establish diplomatic relations ?",
            "In what year did Hitler gain power of Germany ?",
            "In what year did Ireland elect its first woman president ?",
            "In what year did Joe DiMaggio compile his 56-game hitting streak ?",
            "In what year did Thatcher become prime minister ?",
            "In what year did Thatcher gain power ?",
            "In what year did the Bounty mutiny happen ?",
            "In what year did the US Marine Corps adopt the motto `` Semper Fidelis '' ?",
            "In what year did they build the Berlin Wall ?",
            "In what year was De Gaulle elected president of France ?",
            "In what year was Gandhi assassinated ?",
            "In what year was actress Joan Collins born ?",
            "In what year was the Berlin Wall erected ?",
            "In what year was the Wall built ?",
            "In what year was the cannon invented ?",
            "In what year was the first patent for the pull-tab opener on cans obtained ?",
            "In what year was the movie the Ten Commandments released ?",
            "In which year was New Zealand excluded from the ANZUS alliance ?",
            "In which year was the cartoon character Chilly Willy created ?",
            "The Olympic Games in which year allowed Nadia Comaneci to become popular ?",
            "The film `` Jaws '' was made in what year ?",
            "CNN began broadcasting in what year ?",
            "Hitler came to power in Germany in what year ?",
            "What year did Apartheid start ?",
            "What year did Charles Dicken die ?",
            "What year did Degas create the bronze sculpture , `` Fourth Position Front ? ''",
            "What year did Germany sign its nonaggression pact with the Soviet Union ?",
            "What year did Hitler die ?",
            "What year did Jack Nicklaus join the Professional Golfers Association tour ?",
            "What year did Montana become a state ?",
            "What year did Rossetti paint `` Beata Beatrix '' ?",
            "What year did Spielberg make `` Jaws '' ?",
            "What year did nylon stockings first go on sale ?",
            "What year did the United States pass the Copyright law ?",
            "What year did the Vietnam War end ?",
            "What year did the War of 1812 begin ?",
            "What year did the first issue of `` Playboy '' come out ?",
            "What year is etched on the Gold Medal of Excellence from the Paris Exposition depicted on a can of Campbell 's tomato soup ?",
            "What year was Desmond Mpilo Tutu awarded the Nobel Peace Prize ?",
            "What year was Janet Jackson 's first album released ?",
            "What year was the ATM first introduced ?",
            "What year was the Avery Dennison company founded ?",
            "What year was the NAACP founded ?",
            "What year was the first automobile manufactured ?",
            "What year was the setting for American Graffiti ?",
            "What year were the Olympic Games played in where Nadia Comaneci became popular ?",

            "What date did Neil Armstrong land on the moon ?",
            "What date was Dwight D. Eisenhower born ?",
            "What is the date of Mexico 's independence ?",
            "On what date did Rosa Parks Become a symbol of the civil rights movement for refusing to give up her seat on the bus ?",
            "On which date is the Ukrainians ' Christmas ?",
            "On which dates does the running of the bulls occur in Pamplona , Spain ?",
            "Boxing Day is celebrated on what date ?",
            "CNN 's first broadcast occurred on what date ?",
            "What date did man first land on the moon ?",
            "What date is Boxing Day ?",
            "What date is Richard Nixon 's birthday ?",
            "What is the date of Bastille Day ?",
            "What is the date of Boxing Day ?",
            "What was the date of CNN 's first broadcast ?",
            "What was the date of Iraq 's invasion of Kuwait ?",
            "What is the average date when most malls begin putting up Christmas holiday decorations ?",

            "What day and month did John Lennon die ?",
            "In 1990 , what day of the week did Christmas fall on ?",
            "On what day were John F and Jackie Kennedy married ?",
            "What 's the first day of the week ?",
            "The Iraqis launched their attack on Kuwait on what day ?",
            "What day is August 13 , 1971 ?",
            "What day is known as the `` national day of prayer '' ?",
            "What day of the week sees the most fatal car accidents ?",
            "What day of the week was July 13 ?",
            "What day was Pearl Harbor attacked in 1942 ?",
            "What is the first day of the week ?",

            "What 's the third month of the Gregorian calendar ?",
            "What are the three winter months in the southern hemisphere ?",
            "What month 's third weekend is the Monterey Jazz Festival held on ?",
            "What month , date , and year did Charles I die ?",
            "What month did the Edmund Fitzgerald sink ?",
            "What month of the year is there no television in Iceland ?",
            "What month were you born in if your birthstone is sardonyx ?",

            "What century 's the setting for TV 's The Adventures of Robin Hood ?",
            "What century did art 's Romantic Period begin in ?",
            "What century does Captain Video live in ?",

            "During which season do most thunderstorms occur ?",
            "What season begins with the vernal equinox ?",
            "What season does a hiemal activity normally take place in ?",
            "What season is the setting for Shakespeare 's Midsummer Night 's Dream ?",
            "What is the busiest air travel season ?",

            "What time of day did Emperor Hirohito die ?",
            "What time of year do most people fly ?",
            "What time of year has the most air travel ?",
            "What time of year is air travel the heaviest ?",

            "When did Elvis Presley die ?",
            "When did Hawaii become a state ?",
            "When did Idaho become a state ?",
            "When did John F. Kennedy get elected as President ?",
            "When did North Carolina enter the union ?",
            "When did the Hindenberg crash ?",
            "When is Father 's Day ?",
            "When is St. Patrick 's Day ?",
            "When is hurricane season in the Caribbean ?",
            "When is the official first day of summer ?",
            "When is the summer solstice ?",
            "When was Abraham Lincoln born ?",
            "When was Algeria colonized ?",
            "When was Hiroshima bombed ?",
            "When was Lyndon B. Johnson born ?",
            "When was President Kennedy shot ?",
            "When was Rosa Parks born ?",
            "When was Thomas Jefferson born ?",
            "When was Ulysses S. Grant born ?",
            "When was the Boston tea party ?",
            "When was the first Wal-Mart store opened ?",
            "When was the first kidney transplant ?",
            "When was the first liver transplant ?",
            "When was the first stamp issued ?",
            "When was the telephone invented ?",
            "When were William Shakespeare 's twins born ?",
            "When are sheep shorn ?",
            "When are the Oscars Academy Awards in 1999 ?",
            "When did Aldous Huxley write , `` Brave New World '' ?",
            "When did Amtrak begin operations ?",
            "When did CNN begin broadcasting ?",
            "When did CNN go on the air ?",
            "When did Charles Lindbergh die ?",
            "When did Fraze get his first patent for the pull-tab can ?",
            "When did French revolutionaries storm the Bastille ?",
            "When did Gothic art and architecture flourish ?",
            "When did Hitler come to power in Germany ?",
            "When did Iraqi troops invade Kuwait ?",
            "When did Israel begin turning the Gaza Strip and Jericho over to the PLO ?",
            "When did Jaco Pastorius die ?",
            "When did Lucelly Garcia , a former ambassador of Columbia to Honduras , die ?",
            "When did Mount St. Helen last have a major eruption ?",
            "When did Mount St. Helen last have a significant eruption ?",
            "When did Mount St. Helens last erupt ?",
            "When did Muhammad live ?",
            "When did Nixon die ?",
            "When did Nixon visit China ?",
            "When did Nostradamus believe World War III would begin ?",
            "When did President Kennedy , Lee Harvey Oswald , and Jack Ruby all die ?",
            "When did Princess Diana and Prince Charles get married ?",
            "When did Rococo painting and architecture flourish ?",
            "When did Spain and Korea start ambassadorial relations ?",
            "When did Spielberg direct `` Jaws '' ?",
            "When did Thatcher become prime minister ?",
            "When did Theo Rousseau paint the `` Forest of Fontaine '' ?",
            "When did World War I start ?",
            "When did beethoven die ?",
            "When did communist control end in Hungary ?",
            "When did humans first begin to write history seriously ?",
            "When did swimming become commonplace ?",
            "When did the American Civil War end ?",
            "When did the Berlin Wall go up ?",
            "When did the Bounty mutiny take place ?",
            "When did the Carolingian period begin ?",
            "When did the Chernobyl nuclear accident occur ?",
            "When did the Dow first reach ?",
            "When did the Jurassic Period end ?",
            "When did the `` Star-Spangled Banner '' become the national anthem ?",
            "When did the art of quilting begin ?",
            "When did the last Americans leave Vietnam ?",
            "When did the neanderthal man live ?",
            "When did the original Howdy Doody show go off the air ?",
            "When did the royal wedding of Prince Andrew and Fergie take place ?",
            "When did the supercontinent Pangaea break up ?",
            "When did the use of `` the syringe '' first appear in medicinal history ?",
            "When did the vesuvius last erupt ?",
            "When did they canonize the Bible ?",
            "When do MORMONS believe Christ was born ?",
            "When do you plant winter wheat ?",
            "When does menstruation begin ?",
            "When does the Bible say the seasons started ?",
            "When does the average teenager first have intercourse ?",
            "When is Bastille Day ?",
            "When is Boxing Day ?",
            "When is Dick Clark 's birthday ?",
            "When is President Nixon 's birthday ?",
            "When is a woman most fertile ?",
            "When is the Jimmy Buffett concert coming to the E center in Camden NJ ?",
            "When is the Sun closest to the Earth ?",
            "When is the Thai New Year ?",
            "When is the Tulip Festival in Michigan ?",
            "When is the site www.questions.com going to open ?",
            "When was Babe Ruth born ?",
            "When was Beethoven born ?",
            "When was Berlin 's Brandenburg gate erected ?",
            "When was CNN 's first broadcast ?",
            "When was Calypso music invented ?",
            "When was China 's first nuclear test ?",
            "When was Christ born ?",
            "When was Dick Clark born ?",
            "When was Dubai 's first concrete house built ?",
            "When was Florida admitted into the Union ?",
            "When was Franklin D. Roosevelt stricken with polio ?",
            "When was General Manuel Noriega ousted as the leader of Panama and turned over to U.S. authorities ?",
            "When was Hurricane Hugo ?",
            "When was John D. Rockefeller born ?",
            "When was London 's Docklands Light Railway constructed ?",
            "When was Microsoft established ?",
            "When was Nostradamus born ?",
            "When was Ozzy Osbourne born ?",
            "When was Queen Victoria born ?",
            "When was Richard Nixon born ?",
            "When was Yemen reunified ?",
            "When was `` the Great Depression '' ?",
            "When was child labor abolished ?",
            "When was cigarette advertising banned on television and radio ?",
            "When was the Battle of Hastings ?",
            "When was the Berlin Wall erected ?",
            "When was the Big Thompson flood ?",
            "When was the Bill of Rights ratified ?",
            "When was the Brandenburg Gate in Berlin built ?",
            "When was the Congress of Vienna ?",
            "When was the De Beers company founded ?",
            "When was the G7 group of nations formed ?",
            "When was the Hoover Dam constructed ?",
            "When was the NFL established ?",
            "When was the Parthenon built ?",
            "When was the San Francisco fire ?",
            "When was the Triangle Shirtwaist fire ?",
            "When was the USSR dissolved ?",
            "When was the bar-code invented ?",
            "When was the battle of the Somme fought ?",
            "When was the first American encyclopedia published ?",
            "When was the first Barbie produced ?",
            "When was the first Wall Street Journal published ?",
            "When was the first flush toilet invented ?",
            "When was the first practical commercial typewriter marketed ?",
            "When was the first railroad from the east coast to the west coast completed ?",
            "When was the first stained glass window made ?",
            "When was the first steel mill in the United States built ?",
            "When was the first successful heart transplant for a human ?",
            "When was the internal combustion engine developed ?",
            "When was the last major eruption of Mount St. Helens ?",
            "When was the slinky invented ?",
            "When was the women 's suffrage amendment ratified ?",
            "When were camcorders introduced in Malaysia ?",
            "When were fish first believed to be found on earth ?",
            "When were the Olympic Games in which Nadia Comaneci became popular played ?",
            "When will Jean Aeul publish her next book ?",
            "When will the millennium officially begin ?",

            "What geological time do we live in ?",
            "What is Dick Clark 's birthday ?",
            "What is Dick Clark 's date of birth ?",
            "What is Judy Garland 's date of birth ?",
            "What is Martin Luther King Jr. 's real birthday ?",
            "What is President Nixon 's birthdate ?",
        ]

        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_DATE,
                          predict_question_type(q))

    def test_numeric_count(self):
        test = [
            # "What 's the American dollar equivalent for 8 pounds in the U.K. ?",

            "What 's the maximum number of clubs a golfer may use in a round ?",
            "What is the average hours per months spent online by AOL users ?",
            "What is the chromosome number of an elephant ?",

            "What 's the population of Biloxi , Mississippi ?",
            "What 's the population of Mississippi ?",
            "What is the population of Japan ?",
            "What is the population of Kansas ?",
            "What is the population of Mexico ?",
            "What is the population of Mozambique ?",
            "What is the population of Ohio ?",
            "What is the population of the United States ?",
            "What is the population of Venezuela ?",
            "What is the world 's population ?",
            "What is the population of Seattle ?",
            "What is the population of Nigeria ?",
            "What is the population of China ?",
            "What is the population of Australia ?",
            "What is the current population for these countries : France , Spain , Italy , Greece , Austria , Germany , Switzerland , the Netherlands ?",
            "What is the estimated total U.S. whitetail deer population ?",
            "What is the goat population of the world ?",
            "How large is Missouri 's population ?",  # volume
            "What is the approximate population of Las Vegas , N.M ?",
            "What is the student population at the University of Massachusetts in Amherst ?",

            "What is the highest number of home runs on record for any one game ?",
            "What is the most number of goals scored by a single team in an NHL hockey game ?",
            "What is the pig population of the world ?",
            "What is the population in India ?",
            "What is the population of Arcadia , Florida ?",
            "What is the population of the largest Chilean city",
            "What is the world population as of today ?",
            "What was the Great Britain population from 1699-172 ?",
            "What was the U.S. highway death toll in 1969 ?",
            "What is the death toll of people dying from tuberculosis ?",
            "What was the death toll at the eruption of Mount Pinatubo ?",
            "What was the number of assassinations and attempts to assassinate in the U.S. since 1865 ?",

            "How many feet in a mile ?",
            "How many Admirals are there in the U.S. Navy ?",
            "How many Great Lakes are there ?",
            "How many gallons of water are there in a cubic foot ?",
            "How many hearts does an octopus have ?",
            "How many liters in a gallon ?",
            "How many pounds in a ton ?",
            "A normal human pregnancy lasts how many months ?",
            "About how many Americans are still unaccounted for from the Vietnam war ?",
            "About how many soldiers died in World War II ?",
            "Approximately how many students are enrolled at the University of Massachusetts ?",
            "How many American actors were nominated for the best actor Oscar for 1983 ?",
            "How many American soldiers are stationed in South Korea ?",
            "How many American soldiers have died for their country to date ?",
            "How many American soldiers remain unaccounted from the Vietnam war ?",
            "How many Americans fought for the British in the American Revolution ?",
            "How many Americans have HIV ?",
            "How many Beanie Baby sites are there ?",
            "How many Beatles ' records went #1 ?",
            "How many CDs has Garth Brooks sold ?",
            "How many Canadians emmigrate each year ?",
            "How many Community Chest cards are there in Monopoly ?",
            "How many Fig Newtons are there to the pound ?",
            "How many Grammys did Michael Jackson win in 1983 ?",
            "How many Gutenberg Bibles are there ?",
            "How many Israeli athletes were killed at the Munich Olympics ?",
            "How many James Bond novels are there ?",
            "How many Jews were executed in concentration camps during WWII ?",
            "How many John Deere tractors have been manufactured ?",
            "How many Leos have been Pope ?",
            "How many Marx Brothers were there ?",
            "How many Russians have landed on the moon ?",
            "How many South American countries have the letter Z in their names ?",
            "How many Stradivarius violins were ever made ?",
            "How many Superbowls have the ers won ?",
            "How many U.S. presidents were assassinated during Queen Victoria 's reign ?",
            "How many URL extensions are there ? and what are they ?",
            "How many Vietnamese were there in the Soviet Union ?",
            "How many `` No '' answers was the What 's My Line ? panel allowed ?",
            "How many `` eyes '' does a coconut have ?",
            "How many acres in a mile ?",
            "How many airline schools are there in the U.S. ?",
            "How many astronauts have been on the moon ?",
            "How many astronauts manned each Project Mercury flight ?",
            "How many athletes did Puerto Rico enter in the 1984 Winter Olympics ?",
            "How many bails are there in a cricket wicket ?",
            "How many bends are there in a standard paper clip ?",
            "How many blacks served in the Vietnam War",
            "How many bones are in the human hand ?",
            "How many bones are there in the human hand ?",
            "How many bottles of wine were prisoners in the Bastille allowed per day ?",
            "How many boys play the game in Winslow Homer 's 1872 painting Snap the Whip ?",
            "How many bytes are in a terabyte ?",
            "How many cables support the main span of the Golden Gate Bridge ?",
            "How many calories are in a tomato ?",
            "How many calories are there in a Big Mac ?",
            "How many calories are there in a glass of water ?",
            "How many calories are there in soy sauce ?",
            "How many cards are dealt to each player in Gin Rummy ?",
            "How many cards is each player dealt in Contract Bridge ?",
            "How many casinos are in Atlantic City , NJ ?",
            "How many chairs are shown in Vincent Van Gogh 's 188 work The Artist 's Room in Arles ?",
            "How many characters are in the Chinese alphabet ?",
            "How many characters makes up a word for typing test purposes ?",
            "How many chemical elements are there ?",
            "How many cherubs are there on a Trivial Pursuit board ?",
            "How many children does Ray Davies of the Kinks have ?",
            "How many children under 18 are victims of some sort of Physical Abuse each year ?",
            "How many cities are there in Utah ?",
            "How many claws has a lobster called a pistol lost ?",
            "How many colleges are in Wyoming ?",
            "How many colonies did Germany get to keep after World War I ?",
            "How many colonies were involved in the American Revolution ?",
            "How many colored squares are there on a Rubik 's Cube ?",
            "How many colors are there in a rainbow ?",
            "How many colors are there in the spectrum ?",
            "How many colors was the 1940s collectible called a Donald Duck Rubber Boat ?",
            "How many consecutive baseball games did Lou Gehrig play ?",
            "How many continents are there ?",
            "How many copies of an album must be sold for it to be a gold album ?",
            "How many corners does a spritsail have ?",
            "How many counties are in Indiana ?",
            "How many countries are there ?",
            "How many countries watch MTV Europe ?",
            "How many cubic feet of space does a gallon of water occupy ?",
            "How many cullions does a male have ?",
            "How many days does a typical mayfly live ?",
            "How many degrees cooler is the inside of a cucumber than the air outside ?",
            "How many different countries export coffee ?",
            "How many different kinds of ice cream are there ?",
            "How many different languages are spoken in Europe ?",
            "How many different types of skunks are there ?",
            "How many different vegetation zones are there ?",
            "How many disks does each player have in a four-handed game of Crokinole ?",
            "How many dogs pull a sled in the Iditarod ?",
            "How many dollars a day did Arthur Frommer say you could get by on in Europe in 1968 ?",
            "How many dots make up the symbol for `` because '' ?",
            "How many double-word-score spaces are there on a Scrabble Crossword Game board ?",
            "How many e-commerce companies are started every day ?",
            "How many earthworms are in a single pasture ?",
            "How many electoral college votes does Colorado have ?",
            "How many electoral votes does it take to win presidency ?",
            "How many elephants are left on earth ?",
            "How many elevators do you ride to reach the top floor of the Empire State Building ?",
            "How many emperors were there in the Roman Empire ?",
            "How many endangered species are there in the world ?",
            "How many engines does a Boeing 737 have ?",
            "How many equal angles are there in an isosceles triangle ?",
            "How many equal sides are there on a scalene triangle ?",
            "How many events make up the decathlon ?",
            "How many eyes does a bat have ?",
            "How many feet are there in a fathom ?",
            "How many feet high is the hurdle in front of a runner 's steeplechase water jump ?",
            "How many feet long is a baseball pitcher 's rubber ?",
            "How many feet more than 2 is the average height of the Great Wall of China ?",
            "How many fiddlers did Old King Cole have ?",
            "How many films are made by the major studios in a year ?",
            "How many films did Ingmar Bergman make ?",
            "How many fingers are used to draw a bow ?",
            "How many flavors does Baskin & Robbins offer ?",
            "How many flavors of ice cream does Howard Johnson 's have ?",
            "How many frames does a disk camera shoot ?",
            "How many freckles does Howdy Doody have on his face ?",
            "How many furlongs are there in a mile-and-a-quarter recetrack ?",
            "How many gallons of paint does it take to paint the Golden Gate Bridge ?",
            "How many gallons of water go over Niagra Falls every second ?",
            "How many games are played in a five-team round-robin tournament ?",
            "How many grooves are on a dime 's edge ?",
            "How many grooves are on a dime ?",
            "How many hands does Bjorn Borg use when hitting his forehand ?",
            "How many head injuries are there in recreational ice skating each year ?",
            "How many hearts does an octopus have ?",
            "How many holes are there in a tenpin bowling ball ?",
            "How many home runs did Babe Ruth hit in his lifetime ?",
            "How many home runs did Lou Gehrig have during his career ?",
            "How many horses are there on a polo team ?",
            "How many horses died during the civil war ?",
            "How many hostages were killed in the Entebbe raid ?",
            "How many hours of work does it take a typist to complete a 100-page screenplay ?",
            "How many hummingbird eggs could fit in one ostrich egg ?",
            "How many inches apart are adjacent pins in tenpin bowling ?",
            "How many inches over six feet is Tom Selleck ?",
            "How many inches over six feet is the Venus de Milo ?",
            "How many inches tall is Stuart Little at birth ?",
            "How many innings are there in a regulation softball game ?",
            "How many innings constitute an official baseball game ?",
            "How many islands does Fiji have ?",
            "How many islands make up Antigua ?",
            "How many lakes are there on the Earth ?",
            "How many languages are there in the world ?",
            "How many languages does the Pope speak ?",
            "How many lawyers are there in the state of New Jersey ?",
            "How many layers does a bottle of Yoo-Hoo settle into ?",
            "How many layers of yellow paint is a Faber Mongol pencil lucky enough to be sprayed with ?",
            "How many letters appear with the numbers 2 to 9 on a telephone dial ?",
            "How many liberty bells have there been ?",
            "How many logarithmic scales are there on a slide rule ?",
            "How many maids were milking ?",
            "How many major Nazi leaders went on trial after the war at Nuremberg ?",
            "How many megawatts will the power project in Indonesia , built by a consortium headed by Mission Energy of US , produce ?",
            "How many member states are in the UN ?",
            "How many members are in the California congressional delegation ?",
            "How many members of a family could be drafted in the U.S. military during World War II ?",
            "How many men died building the Mackinaw Bridge ?",
            "How many meters are in a mile ?",
            "How many miles are there between Tel Aviv , Israel and Memphis , Tennessee ?",
            "How many miles is it from Frankfurt , Germany to Salzburg , Austria ?",
            "How many miles is it from London , England to Plymouth , England ?",
            "How many miles is it from NY to Austria ?",
            "How many miles is it to Ohio from North Carolina ?",
            "How many miles of corridors are in The Pentagon ?",
            "How many miles of veins are in the circulatory system ?",
            "How many milligrams are in a gram ?",
            "How many millimeters are in a mile ?",
            "How many milliseconds in a second ?",
            "How many mines can still be found in the Falklands after the war ended ?",
            "How many minutes were there on the original GE College Bowl clock ?",
            "How many months does a normal human pregnancy last ?",
            "How many months does it take the moon to revolve around the Earth ?",
            "How many more weeks of winter are there if a ground hog sees his shadow ?",
            "How many mountains have been named for Presidents in the continental USA ?",
            "How many movies has Drew Barrymore been in ?",
            "How many muscles does an oyster have ?",
            "How many muscles does the average adult use when going for a walk ?",
            "How many names are there for Eskimo people ?",
            "How many neurons are in the human brain ?",
            "How many objects orbit the Earth ?",
            "How many oceans are there and name them ?",
            "How many of every 10 members of the Rodeo Cowboys Association have never worked a ranch ?",
            "How many of them are in sub-Saharan Africa ?",
            "How many pairs of legs does a lobster have ?",
            "How many pairs of wings does a tsetse fly have ?",
            "How many penny-farthings are there on a Trivial Pursuit game board ?",
            "How many people are taller than 7 feet ?",
            "How many people are there in the world ?",
            "How many people did Randy Craft kill ?",
            "How many people did Randy Craft murder ?",
            "How many people did Randy Steven Craft murder ?",
            "How many people did the United Nations commit to help restore order and distribute humanitarian relief in Somalia in September 1992 ?",
            "How many people die from snakebite poisoning in the U.S. per year ?",
            "How many people die from tuberculosis each year ?",
            "How many people die of tuberculosis yearly ?",
            "How many people died because of a smoking problem in 1997 ?",
            "How many people died in the Vietnam war ?",
            "How many people died on D-Day ?",
            "How many people died on South Carolina highways in 1998 ?",
            "How many people died when the Estonia sank in 1994 ?",
            "How many people does Honda employ in the U.S. ?",
            "How many people have been Captain America ?",
            "How many people have been killed in wars , armed conflicts ?",
            "How many people have died of tuberculosis ?",
            "How many people hike ?",
            "How many people in America snore ?",
            "How many people in Tucson ?",
            "How many people in the USA say their number one source of information is the newspaper ?",
            "How many people in the world speak French ?",
            "How many people live in Chile ?",
            "How many people live in Tokyo ?",
            "How many people live in cities ?",
            "How many people live in the Falklands ?",
            "How many people lived in Nebraska in the mid 1900s ?",
            "How many people on the ground were killed from the bombing of Pan Am Flight 103 over Lockerbie , Scotland , December 21 , CD .",
            "How many people own pets ?",
            "How many people visit the Pope each month ?",
            "How many people was Randy Craft convicted of killing ?",
            "How many people was Randy Craft convicted of murdering ?",
            "How many people watch network television ?",
            "How many people were executed for Abraham Lincoln 's assassination ?",
            "How many pins are used in skittles ?",
            "How many pitchers occupy the shelf beside the crouching woman in Edgar Degas 's 1886 painting The Tub ?",
            "How many points are there on a Backgammon board ?",
            "How many points is a bullseye worth in darts ?",
            "How many points is a disk in the center hole worth in Crokinole ?",
            "How many points make up a perfect fivepin bowling score ?",
            "How many presidents have died on the 4th of July ?",
            "How many propellers helped power the plane the Wright brothers flew into history ?",
            "How many quarters equal a pound ?",
            "How many quarts of whole milk is needed to make one pound of butter ?",
            "How many queen bees reign in a hive ?",
            "How many questions are on this thing ?",
            "How many questions do you have on your database ?",
            "How many real fruit juices are there in a can of Hawaiian Punch ?",
            "How many referees work a soccer game ?",
            "How many revolutions does a standard LP make in three minutes ?",
            "How many rings are there on a five-zone archery target ?",
            "How many rows of sprocket holes does a roll of 35-millimeter film have ?",
            "How many rows of whiskers does a cat have ?",
            "How many school districts are there in the United States ?",
            "How many seats does the Batmobile sport ?",
            "How many shillings more than 2 were there in a guinea ?",
            "How many shots can a stock M16 hold ?",
            "How many sides does a heptagon have ?",
            "How many sides does an obelisk have ?",
            "How many small businesses are there in the U.S .",
            "How many small businesses are there in the United States ?",
            "How many soldiers were involved in the last Panama invasion by the United States of America ?",
            "How many sonnets did Shakespeare write ?",
            "How many spaces follow a period at the end of a sentence ?",
            "How many spears are there on Kenya 's flag ?",
            "How many species of sharks are there ?",
            "How many species of the Great White shark are there ?",
            "How many sperm cells are in an average ejaculation ?",
            "How many square feet is Bill Gates ' home ?",
            "How many stars are there in Big Dipper ?",
            "How many stars are there on the Soviet Union 's flag ?",
            "How many states did Richard Nixon carry in 1972 ?",
            "How many states have a `` lemon law '' for new automobiles ?",
            "How many states have a lottery ?",
            "How many stations do you shoot from in the basketball game `` Around the World '' ?",
            "How many students attend the University of Massachusetts ?",
            "How many syllables are there in a line of hendecasyllabic poetry ?",
            "How many teaspoons make up a tablespoon ?",
            "How many teats does a female goat sport ?",
            "How many tenths of the Earth 's surface lie under water ?",
            "How many thousands of students attend the University of Massachusetts ?",
            "How many three-letter permutations can be made from the four letters : c ?",
            "How many tiles did the Space Shuttle Columbia lose on its second flight ?",
            "How many times a day does the typical person go to the bathroom ?",
            "How many times a day should you take a prescription marked `` q.i.d . '' ?",
            "How many times a year does the American Gourd Society publish The Gourd ?",
            "How many times can a nickel-cadmium rechargeable battery be recharged ?",
            "How many times does the tide ebb and flow each day ?",
            "How many times has Harold Stassen announced a drive for the White House ?",
            "How many times has `` Louie , Louie '' been recorded ?",
            "How many times in his 16-year National Basketball Associaton career was John Havlicek a member of the all-star team ?",
            "How many times larger than life size is the Statue of Liberty ?",
            "How many times more than 3",
            "How many times was pitcher , Warren Spahn , a 20-game winner in his 21 major league seasons ?",
            "How many trees go into paper making in a year ?",
            "How many types of cheese are there in France ?",
            "How many types of dogs ' tails are there - three",
            "How many types of lemurs are there ?",
            "How many varieties of apple are there ?",
            "How many varieties of twins are there ?",
            "How many verses are in the Bible ?",
            "How many villi are found in the small intestine ?",
            "How many visitors go to the Vatican each year ?",
            "How many votes in Congress dissented from the 1941 declaration of war with Japan ?",
            "How many warmup pitches does a reliever get coming into a baseball game ?",
            "How many watts make a kilowatt ?",
            "How many web servers are there ?",
            "How many websites are there in the world ?",
            "How many were in attendance at the Last Supper ?",
            "How many wings does a flea have ?",
            "How many wives did Brigham Young have ?",
            "How many words are there in the Spanish language ?",
            "How many yards are in 1 mile ?",
            "How many years ago did Led Zeppelin release its last album ?",
            "How many years ago did the ship Titanic sink ?",
            "How many years did Shea & Gould practice law in Los Angeles ?",
            "How many years did Sleeping Beauty sleep ?",
            "How many years did it take James Joyce to write Ulysses ?",
            "How many years do fossils take to form ?",
            "How many years is Johnnie Walker Black Label aged ?",
            "How many years make up a lustrum ?",
            "How many years of bad luck follow breaking a mirror ?",
            "How many years of schooling after highschool does it take to become a neurosurgeon ?",
            "How many years old is Benny Carter ?",
            "How many zeros are there in a trillion ?",
            "How many zip codes are there in the U.S. ?",
            "In South Korea , how many American Soldiers are there ?",
            "On average , how many miles are there to the moon ?",
            "The Shea & Gould law firm had an office in L.A. for how many years ?",

            "How often are brain cells replaced ?",

            "How much of an apple is water ?",
            "How much fiber should you have per day ?",
            "How much Coca Cola is drunk in one day in the world ?",
            "How much caffeine is in a 16 oz cup of coffee ?",
            "How much calcium should an adult female have daily ?",
            "How much electricity does the brain need to work ?",
            "How much energy is released when oxygen and hydrogen mix ?",
            "How much folic acid should a pregnant woman get each day ?",
            "How much folic acid should an expectant mother get daily ?",
            "How much in miles is a ten K run ?",
            "How much iron is in your body ?",
            "How much of the earth 's surface is permanently frozen ?",
            "How much of the nation 's children between the ages of two and eleven watch ` The Simpsons ' ?",
            "How much of the silver production is manufactured by independent silversmiths ?",
            "How much pizza do Americans eat in a day ?",
            "How much salt is in the oceans ?",
            "How much snow equals an inch of rain ?",
            "How much stronger is the new vitreous carbon material invented by the Tokyo Institute of Technology compared with the material made from cellulose ?",
            "How much time does the blinking of an eye take ?",
            "How much waste does an average dairy cow produce in a day ?",
            "How much will the California be in the year 2000 ?",
        ]
        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_COUNT,
                          predict_question_type(q))

    def test_numeric_money(self):
        test = [
            "How much was a ticket for the Titanic ?",
            "By how much will the California state gas tax rise by the year 2000 ?",
            "How much can a person be fined for having a dog on a beach ?",
            "How much could you rent a Volkswagen bug for in 1966 ?",
            "How much did Alaska cost when bought from Russia ?",
            "How much did Lucy Van Pelt originally charge for psychiatric sessions ?",
            "How much did Manchester United spend on players in 1993 ?",
            "How much did Mercury spend on advertising in 1993 ?",
            "How much did Varian Associates try to sell its vacuum products division to the BOC group for ?",
            "How much did a McDonald 's hamburger cost in 1963 ?",
            "How much did the Iran-Contra investigation cost ?",
            "How much did the first Barbie doll sell for in 1959 ?",
            "How much did the minimum wage amount to in 1991 ?",
            "How much do drugs to treat tuberculosis cost ?",
            "How much do tuberculosis combatting drugs cost ?",
            "How much does a new railroad coal car cost ?",
            "How much does it cost , average or whatever is available , to produce and send junk mail catalogues in the US ? , DT CD NN NN ,",
            "How much does it cost to have a tree planted by dialing , 900 , 740-TREE ?",
            "How much does one ton of cement cost ?",
            "How much does the President get paid ?",
            "How much is Clara Peller being paid by Wendy 's to say `` Where 's the beef '' ?",
            "How much is a Canadian 1967 twenty dollar gold coin worth ?",
            "How much money are Dumbo 's ears insured for ?",
            "How much money can a person be fined for having a dog on a beach ?",
            "How much money did the Marcos steal from their country ?",
            "How much money does a back injury lawsuit get ?",
            "How much money does each player get at the beginning of the game in Monopoly ?",
            "How much money does the Sultan of Brunei have ?",
            "How much money was the minimum wage in 1991 ?",
            "How much was the minimum wage in 1991 ?",
            "How much will gas be taxed in California by the year 2000 ?",
            "How much would a black-and-white 1-cent stamp be worth , Thomas Jefferson on it ?",
            "How much would it cost to purchase a 2-foot-square party tent , with sides , ?",

            "Mexican pesos are worth what in U.S. dollars ?",
            "Dialing , 900 , 740-TREE to have a tree planted will cost how much ?",
            "What amount of money did the Philippine ex-dictator Marcos steal from the treasury ?",
            "What are bottle caps with presidents ' pictures inside worth ?",
            "What can you be fined for having a dog on a beach ?",
            "What debts did Qintex group leave ?",
            "What does an average daycare provider get paid in New England ?",
            "What does each of the utilities cost in Monopoly ?",
            "What is average salary of restaurant manager in United States ?",
            "What is the amount of money owed for illegally having a dog on a beach ?",
            "What is the average salary of a paleontologist ?",
            "What is the cost of the drugs used in tuberculosis treatments ?",
            "What is the current ticket fare from from Cairo to Barbados ?",
            "What is the fare cost for the round trip between New York and London on Concorde ?",
            "What is the federal minimum wage ?",
            "What is the fine for having a dog on a beach ?",
            "What is the mean income of the top 10% , top 5% , and top 1% ?",
            "What is the per-capita income of Colombia , South America ?",
            "What is the price for AAA 's liability auto insurance ?",
            "What is the price for tuberculosis drugs ?",
            "What is the regular price ?",
            "What is the salary of a U.S. Representative ?",
            "What is the starting salary for beginning lawyers ?",
            "What is the starting salary of a radiographer ?",
            "What was Joe Namath 's first contract worth ?",
            "What was the 1940 annual salary for a boilermaker ?",
            "What was the first minimum wage ?",
            "What was the minimum wage in 1991 ?",
            "What was the price of Varian Associates ' vacuum products division ?",

            # percentage
            "What is the conversion rate between dollars and pounds ?",
            "What is the exchange rate between England and the U.S. ?",
            "What is the exchange rate for Australian to American money ?",

            "What is the average cost for four years of medical school ?",
            "What will the California gas tax be in the year 2000 ?",
            "What will the increase be in the California gas tax by 2000 ?"
        ]

        for q in test:
            self.assertIn(QuestionSubType.NUMERIC_MONEY,
                          predict_question_type(q))


class TestQuestionsDisambiguation(unittest.TestCase):
    def test_multilabel(self):
        # questions that are correct in more than 1 label
        multi_label = [
            # hum:ind and num:count
            "How many four star generals were there and who are they ?",
            # loc:city or loc:state
            "In What city or state do the most gay men live in ?"
        ]


if __name__ == "__main__":
    unittest.main()
