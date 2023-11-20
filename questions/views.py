from typing import Optional

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.urls import reverse

from .models import Question, Tag
from .forms import CreateQuestionForm


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


class AskQuestion(TopTrendingQuestionsMixin, LoginRequiredMixin, CreateView):
    model = Question
    form_class = CreateQuestionForm
    template_name = 'questions/ask.html'
    login_url = 'login'

    def form_valid(self, form):
        form.instance.author = self.request.user.profile
        form.instance.created = timezone.now()
        new_question = form.save()
        for tag in form.cleaned_data['tag_list']:
            try:
                tag_db = Tag.objects.get(text=tag)
            except Tag.DoesNotExist:
                tag_db = Tag(text=tag)
                tag_db.save()
            new_question.tags.add(tag_db)
        return redirect('questions:question', question_id=new_question.pk)

    def get_success_url(self):
        return reverse(
            'questions:question',
            kwargs=dict(question_id=self.object.pk)
        )


def question(request, question_id: int):
    return HttpResponse(f'Question {question_id} detail info')


class TagPrefixMixin:
    tag_prefix = 'tag:'

    def has_tag_prefix(self, query: str):
        return query.startswith(self.tag_prefix)

    def extract_query(self, query: str):
        return query[len(self.tag_prefix):]

    def with_tag_prefix(self, query: str):
        return self.tag_prefix + query


class SearchByQueryView(TagPrefixMixin, TopTrendingQuestionsMixin, ListView):
    model = Question
    template_name = 'questions/search_results_by_query.html'
    paginate_by = 20
    context_object_name = 'questions'

    def get(self, request):
        query = self.request.GET.get('q')
        if self.has_tag_prefix(query):
            return redirect(
                'questions:tag',
                tag_text=self.extract_query(query)
            )
        return super().get(request)

    def get_queryset(self):
        query = self.request.GET.get('q')
        return Question.objects.search_by_text(query=query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q')
        return context


class SearchByTagView(TagPrefixMixin, TopTrendingQuestionsMixin, ListView):
    model = Question
    template_name = 'questions/search_results_by_tag.html'
    paginate_by = 20
    context_object_name = 'questions'

    def get_queryset(self):
        tag = self.kwargs['tag_text']
        return Question.objects.search_by_tag(tag)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.with_tag_prefix(
            self.kwargs.get('tag_text')
        )
        return context
