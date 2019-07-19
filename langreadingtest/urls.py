from django.urls import path

from . import views

app_name = 'cw'
urlpatterns = [

    # this can be start of test pagel, "start test" should send back request to begin the test properly.
    path('', views.index, name='index'),

    # Ignore the desire for other tests/languages at present
    # Somehow want it under a particular ID though
    # First hard-code testID
    # ex: /2/
    path('<int:quiz_id>/<int:word_id>', views.QuestionView.as_view(), name='chinese_word'),
    # Response from user
    path('<int:quiz_id>/<int:word_id>/answer/', views.answer, name='answer'),
    # path('<int:question_id>/', views.detail, name='detail'),
    path('<int:quiz_id>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:quiz_id>/results/getNumWords', views.get_number_words_estimate, name='number_words'),
]
