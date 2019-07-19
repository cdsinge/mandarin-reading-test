from django.db import models
from django.core.exceptions import ValidationError
import random

def validate_non_empty(some_str):
    if len(some_str) == 0:
        raise ValidationError('Provided String empty')

class ChineseWord(models.Model):
    # BLEURGH, validators aren't called on save(), call full_clean() to run validation.
    simplified = models.CharField(max_length=10, validators=[validate_non_empty])
    pinyin = models.CharField(max_length=30, validators=[validate_non_empty])
    definition = models.CharField(max_length=100, validators=[validate_non_empty])
    pdf = models.FloatField()  # This requires knowing the frequency, to get freq/totalFreq
    # hsk_level = models.IntegerField(default=0)  # 0 for no HSK level
    # traditional = models.CharField(max_length=10)

    def __str__(self):
        return self.simplified

# Would call this Test() but slightly worried that anything with test might cause pytest conflict
# TODO: think of better name/synonym
class Quiz(models.Model):
    # testID (pk automatic?)
    #currentPosition: PopulationSize*0.2
    current_position = models.IntegerField()
    #previousAnswerCorrect: (default) true/false  (direction)
    previous_answer_correct = models.BooleanField(default=True)
    #     moveSize: 0>=x>=1000  (default PopulationSize*0.1)
    step_size = models.IntegerField()  # Consider allowing negative values which would then encode previous_answer_correct
    finished = models.BooleanField(default=False)

    # this is non-optimal in terms of storage-size
    # CSV of already answered questions
    # This might be a list of word IDs, or more likely a list of positions in the test set (depends on implementation)
    correct_list = models.CharField(max_length=300)
    incorrect_list = models.CharField(max_length=300)

    def __str__(self):
        return (self.pk, self.current_position)

    def update_next_word(self, word_id, correct):
        """ Return the next position of the word """
        # Avoid case of reanswering old word
        # This does not avoid that case since current_position is already not present...
        position_of_word_id = self.get_position_at_word_id(word_id)
        if position_of_word_id != self.current_position:
            return self.current_position

        # PRE: correct is a boolean, of whether last answer is correct. TODO assert is boolean
        # Returns next position to be accessed (may be invalid if test over) finished flag on model will be set
        previous_position = self.current_position
        test_size = ChineseWord.objects.all().count()

        # TODO create special case for when know none/all words

        if self.previous_answer_correct == correct:
            self.step_size = round(min(self.step_size * 1.07, test_size * 0.1))
        else:
            # if step size too small, might break down... as requires left has known and right has unknown (not guaranteed in small area)
            self.step_size = round(self.step_size * 0.8)  # round(3*0.85) = 3
        self.previous_answer_correct = correct
        if correct:
            self.add_to_correct_list(self.current_position)
            self.current_position = self.current_position + self.step_size
        else:
            self.add_to_incorrect_list(self.current_position)
            self.current_position = self.current_position - self.step_size
        random_int = random.randint(-1,1)
        self.current_position += random_int

        # Check haven't already used this word
        self.if_already_seen_set_new_position()
        if self.is_finished():
            # Over, so set position to what it finished on
            self.current_position = round((previous_position+self.current_position)/2)
        self.current_position = min(test_size-1, max(0, self.current_position))
        self.save()
        return self.current_position

    def set_finished(self):
        # 3 cases for finishing
        # 1/2 - reached end of the set (either knows all words or no words)
        # 3 - the step size is very small, have homed in to the desired point (TODO statistically work this out)
        test_size = ChineseWord.objects.all().count()
        if self.current_position <= 1 or self.current_position > test_size:
            self.finished = True
        if self.step_size <= 4 or (self.step_size < test_size*0.005):
            self.finished = True

        # Avoid oscillating, degenerate case
        if self.get_number_answered() >= (test_size * 0.1):
            self.finished = True
        self.save()

    def get_number_answered(self):
        seen = self.get_correct_list_as_ints() + self.get_incorrect_list_as_ints()
        return len(seen)

    def is_finished(self):
        self.set_finished()
        return self.finished

    def if_already_seen_set_new_position(self):
        # position is already set in the correct place
        # add some randomness and check word hasn't already been tested
        seen = self.get_correct_list_as_ints() + self.get_incorrect_list_as_ints()
        while self.current_position in seen:
            # Always increasing ism't ideal
            # TODO go to nearest available
            self.current_position += 1
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
        # TODO This doesn't belong in this class
        for index, item in enumerate(ChineseWord.objects.all()):
            if index == position:
                return item.id
        raise RuntimeError('Something went wrong, did not find expected word number {}'.format(
                position))

    def get_word_id_at_current_position(self):
        return self.get_word_id_at_position(self.current_position)

    def get_position_at_word_id(self, word_id):
        for index, item in enumerate(ChineseWord.objects.all()):
            if item.id == word_id:
                return index
        raise RuntimeError('word_id not found {}'.format(word_id))

    def get_number_words(self):
        # The point where we estimate the user's knowledge of a word to be 0.5
        #user_05_probability = quiz.current_position
        word_id = self.get_word_id_at_current_position()
        pdf_at_this_word = ChineseWord.objects.get(pk=word_id).pdf
        # SImply assume that the individual frequency of this point
        # print (pdf_at_this_word)
        # print (0.5/pdf_at_this_word)
        multiplier = (0.5 / pdf_at_this_word)
        number_of_known_words_estimate = 0

        for _, item in enumerate(ChineseWord.objects.all()):
            prob_of_knowing_word = item.pdf * multiplier
            if prob_of_knowing_word > 1:
                prob_of_knowing_word = 1
            number_of_known_words_estimate += prob_of_knowing_word
        """
        Toy example
        11 words, so each word has pdf 1/11 uniform probability
        User has 0.5 at word 6, how many words does the user know...
        1/11  user estimate 0.5 = 5.5/11.   0.5 / pdf = 5.5 here
        This actually breaks down, as even if user knows all the words, it'd still give 5.5...
        """
        return round(number_of_known_words_estimate)
