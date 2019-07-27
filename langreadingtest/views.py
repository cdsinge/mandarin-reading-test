from django.views import generic
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse

from .models import ChineseWord, Quiz, WordDataset, create_quiz
import random
import logging
logging.basicConfig(level=logging.INFO)

class IndexView(TemplateView):
    template_name = 'langreadingtest/quiz_config.html'

# class ConfigureTestView(TemplateView):
#     template_name = 'langreadingtest/quiz_config.html'

#     # def get_context_data(self, **kwargs):
#     #      context = super(ResultsView, self).get_context_data(**kwargs)
#     #      context['quiz'] = Quiz.objects.get(pk=kwargs['quiz_id'])
#     #      return context

# # def index(request):
# #     pass

def start_test(request):
    # So this should have the option to start the test
    # For now simply redirect to what is desired.

    # Get test population size, assume they're ordered by frequency
    logging.info('Starting new quiz')

    # get dataset
    user_ds_choice = request.POST['dataset']
    try:
        word_dataset = WordDataset.objects.get(name=user_ds_choice)
    except:
        logging.exception(f'Request to get dataset failed. Dataset: {user_ds_choice}')
        return HttpResponseRedirect(reverse('cw:test_index'))

    q = create_quiz(word_dataset)
    initial_word_id = q.get_word_id_at_current_position()
    return HttpResponseRedirect(reverse('cw:chinese_word', args=(q.id, initial_word_id,)))

class QuestionView(TemplateView):
    template_name = 'langreadingtest/chinese_word.html'

    def get_context_data(self, **kwargs):
         context = super(QuestionView, self).get_context_data(**kwargs)
         # Want the word details not just the ID
         context['chineseword'] = ChineseWord.objects.get(pk=kwargs['word_id'])
         return context

def answer(request, quiz_id, word_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    # word = get_object_or_404(ChineseWord, pk=word_id)

    choice = request.POST['choice']
    if choice == 'correct':
        correct = True
    elif choice == 'incorrect':
        correct = False
    else:
        logging.exception(f'Unexpected choice {choice}')
        return HttpResponseRedirect(reverse('cw:chinese_word', kwargs={'quiz_id': quiz_id,
                                                                       'word_id': word_id}))

    logging.info(f'Quid ID: {quiz_id}. Word ID: {word_id}, correct: {correct}')

    logging.info(f'{quiz.current_position}, {quiz.step_size}, {quiz.finished}.')
    quiz.update_next_word(word_id, correct)
    logging.info(f'{quiz.current_position}, {quiz.step_size}, {quiz.finished}')
    if quiz.is_finished():
        # Redirect to summary page
        return HttpResponseRedirect(reverse('cw:results', kwargs={'quiz_id': quiz_id}))

    next_word_id = quiz.get_word_id_at_current_position()
    logging.info(f'Next word id: {next_word_id}')

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
