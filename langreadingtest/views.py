from django.views import generic
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse

from .models import ChineseWord, Quiz

def index(request):
    # So this should have the option to start the test
    # For now simply redirect to what is desired.
    initial_word_id = 800
    current_position = 100
    step_size = 100
    q = Quiz(current_position=current_position, step_size=step_size) 
    q.save()  # save seems to initialise id

    return HttpResponseRedirect(reverse('cw:chinese_word', args=(initial_word_id,)))
    #return HttpResponse("Hello, world. You're at the langreadingtest index.")

# def chinese_word(request, word_id):
#     response = "Chinese word ID {} {} {}."
#     cw = ChineseWord.objects.get(pk=word_id)
#     return HttpResponse(response.format(cw.simplified, cw.pinyin, cw.definition))


class DetailView(generic.DetailView):
    """
    More detail on generic views here: https://docs.djangoproject.com/en/2.2/intro/tutorial04/
    # generic.DetailView provides to template_name the instance from "pk" with the name of the model as the instance (default of context_object_name)
    """
    model = ChineseWord
    template_name = 'langreadingtest/chinese_word.html'

    # def get_queryset(self):
    #     """
    #     Excludes any questions that aren't published yet.
    #     """
    #     return Question.objects.filter(pub_date__lte=timezone.now())

def answer(request, word_id):
    word = get_object_or_404(ChineseWord, pk=word_id)
    # return HttpResponse('Erm')

    # Earlier attempt with more client-side data, playing with sessions
    # #https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Sessions
    # counter = request.session.get('counter', 0)
    # request.session['counter'] = counter + 1
    # print (counter)
    # # interesting

    choice = request.POST['choice']
    if choice == 'correct':
        correct = True
    elif choice == 'incorrect':
        correct = False
    else:
        raise RuntimeError('Unexpected choice {}'.format(choice))
    new_word_id = word_id + 1
    if correct:
        return HttpResponseRedirect(reverse('cw:chinese_word', args=(new_word_id,)))
    else:
        return HttpResponseRedirect(reverse('cw:chinese_word', args=(word_id,)))

    # question = get_object_or_404(Question, pk=question_id)
    # try:
    #     selected_choice = question.choice_set.get(pk=request.POST['choice'])
    # except (KeyError, Choice.DoesNotExist):
    #     # Redisplay the question voting form.
    #     return render(request, 'polls/detail.html', {
    #         'question': question,
    #         'error_message': "You didn't select a choice.",
    #     })
    # else:
    #     selected_choice.votes += 1
    #     selected_choice.save()
    #     # Always return an HttpResponseRedirect after successfully dealing
    #     # with POST data. This prevents data from being posted twice if a
    #     # user hits the Back button.
    #     return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
