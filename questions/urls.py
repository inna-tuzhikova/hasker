from django.urls import path

from . import views

app_name = 'questions'

urlpatterns = [
    path('', views.IndexRecentView.as_view(), name='index'),
    path('trending/', views.IndexTrendingView.as_view(), name='index_trending'),
    path('ask/', views.AskQuestion.as_view(), name='ask'),
    path('question/<int:question_id>', views.question, name='question'),
    path('search/', views.SearchByQueryView.as_view(), name='search'),
    path('tag/<str:tag_text>', views.SearchByTagView.as_view(), name='tag'),
]
