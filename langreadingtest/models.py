from django.db import models
from django.core.exceptions import ValidationError
import random
import logging
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

"""
The main model is that each WordDataset is asssociated to many words, and each Quiz has a WordDataset.
TODO generally deal with interface of a Word superclass, to allow different language, which require different viewss
quiz isn't a great name, but don't want to use 'test' to avoid any confusion with code tests
"""

def validate_non_empty(some_str):
    if len(some_str) == 0:
        raise ValidationError('Provided String empty')

class WordDataset(models.Model):
    """Words belong to datasets, e.g. HSK6 dataset.
    Words belong to a single dataset, so some words may be repeated
    Alternative: many-to-many but frequency ordering within a dataset needs consideration,
    as frequency of the same words is not always the same if different sources are used.
    """
    name = models.CharField(max_length=50, validators=[validate_non_empty])

    def get_word_id_at_position(self, position):
        for index, item in enumerate(self.chineseword_set.all()):
            if index == position:
                return item.id
        logging.error(f'Something went wrong, did not find expected word number {position}')
        # TODO need to handle better in case of error, ideally redirect user to start-page
        return item.id

    def get_position_at_word_id(self, word_id):
        """Should be reverse of get_word_id_at_position"""
        for index, item in enumerate(self.chineseword_set.all()):
            if item.id == word_id:
                return index
        logging.error(f'word_id not found {word_id}')
        # TODO need to handle better in case of error, ideally redirect user to start-page
        return index

    def get_test_size(self):
        test_size = self.chineseword_set.all().count()
        if test_size < 10:
            logging.info('Test size is very small - behaviour may be unexpected')
        return test_size

class ChineseWord(models.Model):
    # BLEURGH, validators aren't called on save(), call full_clean() to run validation.
    simplified = models.CharField(max_length=10, validators=[validate_non_empty])
    pinyin = models.CharField(max_length=30, validators=[validate_non_empty])
    definition = models.CharField(max_length=100, validators=[validate_non_empty])
    normalised_freq = models.FloatField()  # This requires knowing the frequency, to get freq/totalFreq
    # hsk_level = models.IntegerField(default=0)  # 0 for no HSK level
    # traditional = models.CharField(max_length=10)
    dataset = models.ForeignKey(WordDataset, on_delete=models.CASCADE)

    def __str__(self):
        return self.simplified

# Would call this Test() but slightly worried that anything with test might cause pytest conflict
# TODO: think of better name/synonym
class Quiz(models.Model):
    # TODO store start and end time (UTC)
    # testID (pk automatic?)
    # Position is the index of the current word in its dataset. Range is 0 to test size -1
    current_position = models.IntegerField()
    previous_answer_correct = models.BooleanField(default=True)
    step_size = models.IntegerField()  # Consider allowing negative values which would then encode previous_answer_correct
    finished = models.BooleanField(default=False)

    # this is non-optimal in terms of storage-size
    # CSV of already answered questions as positions
    # This is a list of positions in the test set
    correct_list = models.CharField(max_length=300)
    incorrect_list = models.CharField(max_length=300)

    word_dataset = models.ForeignKey(WordDataset, on_delete=models.CASCADE)

    def __str__(self):
        return (self.pk, self.current_position)

    def get_test_size(self):
        return self.word_dataset.get_test_size()

    def update_next_word(self, word_id, correct):
        """ Return the next position of the word """

        # Avoid case of reanswering old word, by checking it's the current expected word being answered
        position_of_word_id = self.get_position_at_word_id(word_id)
        if position_of_word_id != self.current_position:
            logging.info(f'Position of word ID {word_id} {position_of_word_id}'\
                         f' not same as current position {self.current_position}')
            return self.current_position

        # logging.debug('Entering position change logic')
        # PRE: correct is a boolean, of whether last answer is correct. TODO assert is boolean
        # Returns next position to be accessed (may be invalid if test over) finished flag on model will be set
        previous_position = self.current_position

        if self.previous_answer_correct == correct:
            self.step_size = round(min(self.step_size * 1.05, self.get_test_size() * 0.1))
        else:
            # if step size too small, might break down... as requires left has known and right has unknown (not guaranteed in small area)
            self.step_size = round(self.step_size * 0.9)  # round(3*0.85) = 3
        self.previous_answer_correct = correct
        if correct:
            self.add_to_correct_list(self.current_position)
            self.current_position = self.current_position + self.step_size
        else:
            self.add_to_incorrect_list(self.current_position)
            self.current_position = self.current_position - self.step_size
        random_int = random.randint(-1,1)
        self.current_position += random_int
        self.current_position = min(self.get_test_size()-1, max(0, self.current_position))

        self.set_finished()

        # Check haven't already used this word
        self.if_already_seen_set_new_position()
        if self.is_finished():
            # Over, so set position to what it finished on
            self.current_position = round((previous_position+self.current_position)/2)
            self.current_position = min(self.get_test_size()-1, max(0, self.current_position))
        self.save()
        return self.current_position

    def set_finished(self):
        # TODO save reason for end of test
        # 3 cases for finishing
        # 1/2 - reached end of the set (either knows all words or no words)
        # 3 - the step size is very small, have homed in to the desired point (TODO statistically work this out)

        if self.get_number_answered() <= 10:  # Insist on a minimum number of answers
            return

        if self.current_position <= 1 or self.current_position > self.get_test_size():
            logging.info('Current position at end of data, end of test')
            self.finished = True
        if self.step_size <= 4 or (self.step_size < self.get_test_size()*0.005):
            logging.info('Step size small, end of test')
            self.finished = True

        # Avoid degenerate case
        if self.get_number_answered() >= (self.get_test_size() * 0.1) or \
           self.get_number_answered() >= 40:
            logging.info('Answered too many questions, end of test')
            self.finished = True
        self.save()

    def get_number_answered(self):
        return len(self.get_seen_list())

    def is_finished(self):
        #self.set_finished()
        return self.finished

    def if_already_seen_set_new_position(self):
        # TODO create unit tests
        # position is already set in the correct place
        # get closest word that has not already been seen
        seen = self.get_correct_list_as_ints() + self.get_incorrect_list_as_ints()
        if len(seen) == self.get_test_size():
            raise RuntimeError('Uh-oh, bad state. Seen all words. This should never happen!')
        increment = 1
        while self.current_position in seen:
            # Always increasing ism't ideal
            # TODO go to nearest available
            self.current_position += increment
            if self.current_position >= self.get_test_size():
                # At end of dataset, start decreasing position.
                self.current_position -= 1
                increment = -1
        self.save()

    def add_to_correct_list(self, pos):
        if len(self.correct_list) == 0:
            self.correct_list += "{}".format(self.current_position)
        else:
            self.correct_list += ",{}".format(self.current_position)
        self.save()

    def add_to_incorrect_list(self, pos):
        if len(self.incorrect_list) == 0:
            self.incorrect_list += "{}".format(self.current_position)
        else:
            self.incorrect_list += ",{}".format(self.current_position)
        self.save()

    def get_seen_list(self):
        return self.get_correct_list_as_ints() + self.get_incorrect_list_as_ints()

    def get_correct_list_as_ints(self):
        # Helper since it's stored as string csv 
        return list(map(int, filter(None, self.correct_list.split(','))))

    def get_incorrect_list_as_ints(self):
        # Helper since it's stored as string csv
        return list(map(int, filter(None, self.incorrect_list.split(','))))

    def get_word_id_at_position(self, position):
        return self.word_dataset.get_word_id_at_position(position)

    def get_word_id_at_current_position(self):
        return self.get_word_id_at_position(self.current_position)

    def get_position_at_word_id(self, word_id):
        return self.word_dataset.get_position_at_word_id(word_id)

    def get_number_words(self):
        # # Attempt 1, has serious shortcomings
        # # Not sure how to use the frequency data, instead simply use the rank order
        # # The point where we estimate the user's knowledge of a word to be 0.5
        # #user_05_probability = quiz.current_position
        # word_id = self.get_word_id_at_current_position()
        # normalised_freq_at_this_word = self.word_dataset.chineseword_set.get(pk=word_id).normalised_freq
        # # Simply assume that the individual frequency of this point
        # multiplier = (0.5 / normalised_freq_at_this_word)
        # number_of_known_words_estimate = 0

        # for _, item in enumerate(self.word_dataset.chineseword_set.all()):
        #     prob_of_knowing_word = item.normalised_freq * multiplier
        #     if prob_of_knowing_word > 1:
        #         prob_of_knowing_word = 1
        #     number_of_known_words_estimate += prob_of_knowing_word

        # # Attempt 2
        # # Isotonic regression for monotonicty (simply using rank order of word relative-frequency)
        # # TODO smooth to cubic scipy.interpolate.PchipInterpolator(x, y, axis=0, extrapolate=None)[source]
        # # TODO adding random points at end for extrapolation a little hacky
        # xs = [-50]+self.get_correct_list_as_ints() + self.get_incorrect_list_as_ints()+[self.get_test_size()+50]
        # ys = ([1]*(1+len(self.get_correct_list_as_ints()))) + \
        #      ([0]*(1+len(self.get_incorrect_list_as_ints())))
        # # Get in position order
        # zipped_sorted = sorted(list(zip(xs,ys)), key = lambda x: x[0])
        # (xs,ys) = zip(*zipped_sorted)

        # ir = IsotonicRegression(y_max=1, y_min=0, increasing=False).fit(xs, ys)
        # number_of_known_words_estimate = int(ir.predict(np.arange(1, self.get_test_size()+1)).sum())

        # # Attempt 3
        # # Not sure how to use the frequency data, instead simply use the rank order
        # # The point where we estimate the user's knowledge of a word to be 0.5
        # #user_05_probability = quiz.current_position
        # word_id = self.get_word_id_at_current_position()
        # normalised_freq_at_this_word = self.word_dataset.chineseword_set.get(pk=word_id).normalised_freq
        # # SImply assume that the individual frequency of this point
        # multiplier = 1.0 / normalised_freq_at_this_word
        # number_of_known_words_estimate = 0

        # def probability_by_multiply_rel_freq_in_odds_space(rel_freq, multiplier):
        #     odds = rel_freq/(1-rel_freq) * multiplier
        #     p = odds/(1+odds)
        #     return p

        # for _, item in enumerate(self.word_dataset.chineseword_set.all()):
        #     prob_of_knowing_word = probability_by_multiply_rel_freq_in_odds_space(item.normalised_freq, multiplier)
        #     if prob_of_knowing_word > 1:
        #         prob_of_knowing_word = 1
        #     number_of_known_words_estimate += prob_of_knowing_word

        # Attempt 4
        # Treat word number as dependent variable, and correct/incorrect as categorical response variable
        # Logistic regression approach        
        xs = [-50]+self.get_correct_list_as_ints() + self.get_incorrect_list_as_ints()+[self.get_test_size()+50]
        ys = ([1]*(1+len(self.get_correct_list_as_ints()))) + \
             ([0]*(1+len(self.get_incorrect_list_as_ints())))
        # Get in position order
        zipped_sorted = sorted(list(zip(xs,ys)), key = lambda x: x[0])
        (xs,ys) = zip(*zipped_sorted)

        logmodel = LogisticRegression(solver='lbfgs')
        logmodel.fit(np.asarray(xs).reshape(-1,1), ys)
        if not (logmodel.classes_ == [0,1]).all():
            logging.error('Unexpected class ordering in logmodel')
        to_predict = np.asarray(range(0, self.get_test_size()-1)).reshape(-1,1)
        predictions = logmodel.predict_proba(to_predict)
        number_of_known_words_estimate = predictions[:,1].sum()
        # Hmm, with this approach how to best choose sampling points.

        return int(number_of_known_words_estimate)

    def get_number_known_words_percent(self):
        return round(100.0/self.get_test_size()*self.get_number_words(), 1)

def create_quiz(word_dataset):
    # Would be nicer for this logic to live with Quiz class
    test_size = word_dataset.chineseword_set.all().count()
    random_int = random.randint(-5,5)
    initial_position = round(test_size*0.5) + random_int
    initial_step_size = round(max(15, test_size*0.04))

    q = Quiz(word_dataset=word_dataset, current_position=initial_position, step_size=initial_step_size)
    q.save()  # save seems to initialise id too 
    return q
