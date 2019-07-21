from django.urls import path

from . import views

app_name = 'cw'
urlpatterns = [
    path('', views.index, name='index'),
    # path('', views.IndexView.as_view(), name='index'),
    # path('create', views.ConfigureTestView.as_view(), name='config'),
    path('<int:quiz_id>/<int:word_id>', views.QuestionView.as_view(), name='chinese_word'),
    path('<int:quiz_id>/<int:word_id>/answer/', views.answer, name='answer'),
    path('<int:quiz_id>/results/', views.ResultsView.as_view(), name='results'),
]
