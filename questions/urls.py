from django.urls import path

from . import views

app_name = 'questions'

urlpatterns = [
    path('', views.IndexRecentView.as_view(), name='index'),
    path('trending/', views.IndexTrendingView.as_view(), name='index_trending'),
    path('ask/', views.AskQuestionView.as_view(), name='ask'),
    path(
        'question/<int:question_id>/answer/<int:answer_id>/upvote',
        views.UpvoteAnswerView.as_view(),
        name='upvote_answer'
    ),
    path(
        'question/<int:question_id>/answer/<int:answer_id>/downvote',
        views.DownvoteAnswerView.as_view(),
        name='downvote_answer'
    ),
    path(
        'question/<int:pk>/upvote',
        views.UpvoteQuestionView.as_view(),
        name='upvote_question'
    ),
    path(
        'question/<int:pk>/downvote',
        views.DownvoteQuestionView.as_view(),
        name='downvote_question'
    ),
    path(
        'question/<int:question_id>/correct/<int:answer_id>',
        views.SetCorrectAnswerView.as_view(),
        name='set_correct_answer'
    ),
    path(
        'question/<int:pk>',
        views.QuestionDetailView.as_view(),
        name='question'
    ),
    path('search/', views.SearchByQueryView.as_view(), name='search'),
    path('tag/<str:tag_text>', views.SearchByTagView.as_view(), name='tag'),
]
