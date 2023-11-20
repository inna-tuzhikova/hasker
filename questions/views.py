from typing import Optional

from django.http import HttpResponse
from django.shortcuts import render, redirect
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
    paginate_by = 2
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


class SearchView(TopTrendingQuestionsMixin, ListView):
    model = Question
    template_name = 'questions/search_results.html'
    paginate_by = 2
    context_object_name = 'questions'
    tag_prefix = 'tag:'

    def get(self, request):
        query = self.request.GET.get('q')
        if query.startswith(self.tag_prefix):
            return redirect(
                'questions:tag',
                tag_text=query[len(self.tag_prefix):]
            )
        return super().get(request)

    def get_queryset(self):
        query = self.request.GET.get('q')
        return Question.objects.search_by_text(query=query)


def tag(request, tag_text: str):
    return HttpResponse(f'Questions with tag `{tag_text}`')
