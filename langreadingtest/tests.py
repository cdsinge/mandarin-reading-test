from django.test import TestCase
from .models import Quiz,ChineseWord

def create_chinese_word_objects(num):
    for i in range(num):
        ChineseWord.objects.create(pdf=0.01)

class QuizTestCase(TestCase):
    def setUp(self):
        create_chinese_word_objects(150)
        current_position = 20
        step_size = 10
        Quiz.objects.create(id=1,
                            current_position=current_position,
                            step_size=step_size)

    def test_quiz_update_new_word_correct_moves_position_forwards(self):
        quiz = Quiz.objects.get(id=1)
        # check set up as expected
        orig_step_size = 10
        self.assertEqual(quiz.current_position, 20)
        self.assertEqual(quiz.step_size, orig_step_size)
        quiz.update_next_word(correct=True)
        self.assertFalse(quiz.finished)
        self.assertGreater(quiz.step_size, orig_step_size)
        self.assertGreaterEqual(quiz.current_position, 30)

    def test_quiz_update_new_word_incorrect_moves_position_backwards(self):
        quiz = Quiz.objects.get(id=1)
        # check set up as expected
        orig_step_size = 10
        self.assertEqual(quiz.current_position, 20)
        self.assertEqual(quiz.step_size, orig_step_size)
        quiz.update_next_word(correct=False)
        self.assertFalse(quiz.finished)
        self.assertLess(quiz.step_size, orig_step_size)
        self.assertLessEqual(quiz.current_position, 13)

    def test_quiz_update_new_word_incorrect_then_correct_decreases_step_size(self):
        quiz = Quiz.objects.get(id=1)
        orig_step_size = 10
        self.assertEqual(quiz.step_size, orig_step_size)
        quiz.previous_answer_correct = False
        quiz.update_next_word(correct=True)
        self.assertLess(quiz.step_size, orig_step_size)

    def test_quiz_update_new_word_correct_then_incorrect_decreases_step_size(self):
        quiz = Quiz.objects.get(id=1)
        orig_step_size = 10
        self.assertEqual(quiz.step_size, orig_step_size)
        quiz.previous_answer_correct = True
        quiz.update_next_word(correct=False)
        self.assertLess(quiz.step_size, orig_step_size)

    def test_quiz_update_new_word_correct_then_correct_increases_step_size(self):
        quiz = Quiz.objects.get(id=1)
        orig_step_size = 10
        self.assertEqual(quiz.step_size, orig_step_size)
        quiz.previous_answer_correct = True
        quiz.update_next_word(correct=True)
        self.assertGreater(quiz.step_size, orig_step_size)

    def test_quiz_update_new_word_incorrect_then_incorrect_increases_step_size(self):
        quiz = Quiz.objects.get(id=1)
        orig_step_size = 10
        self.assertEqual(quiz.step_size, orig_step_size)
        quiz.previous_answer_correct = False
        quiz.update_next_word(correct=False)
        self.assertGreater(quiz.step_size, orig_step_size)

    def test_quiz_update_new_word_correct_adds_to_correct_list(self):
        quiz = Quiz.objects.get(id=1)
        # check set up as expected
        current_position = quiz.current_position
        quiz.update_next_word(correct=True)
        self.assertIn(current_position, quiz.get_correct_list_as_ints())
        self.assertNotIn(current_position, quiz.get_incorrect_list_as_ints())

    def test_quiz_update_new_word_incorrect_adds_to_incorrect_list(self):
        quiz = Quiz.objects.get(id=1)
        # check set up as expected
        current_position = quiz.current_position
        quiz.update_next_word(correct=False)
        self.assertIn(current_position, quiz.get_incorrect_list_as_ints())
        self.assertNotIn(current_position, quiz.get_correct_list_as_ints())

    def test_words_are_ordered_by_id(self):
        # This test doesn't exactly guarantee this, and is useless as an ongoing test
        id = 0
        for cw in ChineseWord.objects.all():
            self.assertGreater(cw.id, id)
            id = cw.id

    def test_get_number_answered_for_some_correct_some_incorrect_case(self):
        quiz = Quiz.objects.get(id=1)
        quiz.correct_list = '2,3,34'
        quiz.incorrect_list = '17,10'
        self.assertEquals(quiz.get_number_answered(), 5)

    def test_get_number_answered_for_empty_case(self):
        quiz = Quiz.objects.get(id=1)
        quiz.correct_list = ''
        quiz.incorrect_list = ''
        self.assertEquals(quiz.get_number_answered(), 0)
