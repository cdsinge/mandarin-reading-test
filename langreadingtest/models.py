from django.db import models
from django.core.exceptions import ValidationError

def validate_non_empty(some_str):
    if len(some_str) == 0:
        raise ValidationError('Provided String empty')

class ChineseWord(models.Model):
    # BLEURGH, validators aren't called on save(), call full_clean() to run validation.
    simplified = models.CharField(max_length=10, validators=[validate_non_empty])
    pinyin = models.CharField(max_length=30, validators=[validate_non_empty])
    definition = models.CharField(max_length=100, validators=[validate_non_empty])

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
    step_size = models.IntegerField()

    # this is non-optimal in terms of storage-size
    # CSV of already answered questions
    correct_list = models.CharField(max_length=300)
    incorrect_list = models.CharField(max_length=300)

    def __str__(self):
        return (self.pk, self.current_position)

# class Question(models.Model):
#     question_text = models.CharField(max_length=200)
#     pub_date = models.DateTimeField('date published')

# class Choice(models.Model):
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     choice_text = models.CharField(max_length=200)
#     votes = models.IntegerField(default=0)
