from django.views import generic
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse

from .models import ChineseWord, Quiz
import random

def index(request):
    # So this should have the option to start the test
    # For now simply redirect to what is desired.

    # Get test population size, assume they're ordered by frequency
    test_size = ChineseWord.objects.all().count()

    current_position = round(test_size*0.2)
    step_size = round(test_size*0.04)
    q = Quiz(current_position=current_position, step_size=step_size) 
    q.save()  # save seems to initialise id

    # Assume at least 10 items in population, introduce randomness to make it a repeatable test
    random_int = random.randint(-5,5)
    initial_word_number = current_position + random_int
    for index, item in enumerate(ChineseWord.objects.all()):
        if index == initial_word_number:
            initial_word_id = item.id
            break
    else:
        raise RuntimeError('Something went wrong, did not find expected word number {}'.format(initial_word_number))
    # because pk is not the same as initial_word_id, find the equivalent
    return HttpResponseRedirect(reverse('cw:chinese_word', args=(q.id, initial_word_id,)))
    #return HttpResponse("Hello, world. You're at the langreadingtest index.")


class QuestionView(TemplateView):
    template_name = 'langreadingtest/chinese_word.html'

    def get_context_data(self, **kwargs):
         context = super(QuestionView, self).get_context_data(**kwargs)
         # Want the word details not just the ID
         context['chineseword'] = ChineseWord.objects.get(pk=kwargs['word_id'])
         return context

def answer(request, quiz_id, word_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    word = get_object_or_404(ChineseWord, pk=word_id)

    choice = request.POST['choice']
    if choice == 'correct':
        correct = True
    elif choice == 'incorrect':
        correct = False
    else:
        raise RuntimeError('Unexpected choice {}'.format(choice))

    print(quiz.current_position, quiz.step_size, quiz.finished)
    next_position = quiz.update_next_word(word_id, correct)
    print(next_position, quiz.step_size, quiz.finished)
    if quiz.is_finished():
        # Redirect to summary page
        return HttpResponseRedirect(reverse('cw:results', kwargs={'quiz_id': quiz_id}))

    next_word_id = quiz.get_word_id_at_position(next_position)

    return HttpResponseRedirect(reverse('cw:chinese_word', kwargs={'quiz_id': quiz_id,
                                                                   'word_id': next_word_id}))

# def get_number_words_estimate(request, quiz_id, word_id):
#     quiz = get_object_or_404(Quiz, pk=quiz_id)
#     word = get_object_or_404(ChineseWord, pk=word_id)
#     pass

class ResultsView(TemplateView):
    template_name = 'langreadingtest/results.html'

    def get_context_data(self, **kwargs):
         context = super(ResultsView, self).get_context_data(**kwargs)
         context['quiz'] = Quiz.objects.get(pk=kwargs['quiz_id'])
         return context
