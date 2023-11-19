from typing import Optional

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView

from .models import Question


class TopTrendingQuestionsMixin:
    top_n = 20
    trending_ctx_name = 'trending'

    @staticmethod
    def get_trending(top_n: Optional[int] = None):
        top_n = top_n or TopTrendingQuestionsMixin.top_n
        return Question.objects.n_trending(top_n=top_n)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.trending_ctx_name] = self.get_trending()
        return context


class IndexView(TopTrendingQuestionsMixin, ListView):
    template_name = 'questions/index.html'
    model = Question
    context_object_name = 'questions'
    paginate_by = 20
    sort_type = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_type'] = self.sort_type
        return context


class IndexRecentView(IndexView):
    sort_type = 'recent'

    def get_queryset(self):
        return Question.objects.recent()


class IndexTrendingView(IndexView):
    sort_type = 'trending'

    def get_queryset(self):
        return Question.objects.trending()


def ask(request):
    return HttpResponse('Ask!')


def question(request, question_id: int):
    return HttpResponse(f'Question {question_id} detail info')


def search(request):
    if request.method == 'GET':
        query = request.GET.get('q')
        return HttpResponse(f'Search results for {query}')


def tag(request, tag_id: int):
    return HttpResponse(f'Questions with tag {tag_id}')
