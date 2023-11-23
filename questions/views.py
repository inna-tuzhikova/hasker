from typing import Optional

from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import ContextMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages

from .models import Question, Tag, Answer
from .forms import CreateQuestionForm, AddAnswerForm


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
        return redirect('questions:question', pk=new_question.pk)

    def get_success_url(self):
        return reverse(
            'questions:question',
            kwargs=dict(question_id=self.object.pk)
        )


@login_required(login_url='login')
def upvote_question(request, pk):
    q = get_object_or_404(Question, pk=pk)
    q.upvote(user=request.user.profile)
    return redirect('questions:question', pk=pk)


@login_required(login_url='login')
def downvote_question(request, pk):
    q = get_object_or_404(Question, pk=pk)
    q.downvote(user=request.user.profile)
    return redirect('questions:question', pk=pk)


@login_required(login_url='login')
def upvote_answer(request, question_id, answer_id):
    a = get_object_or_404(Answer, pk=answer_id)
    a.upvote(user=request.user.profile)
    return redirect('questions:question', pk=question_id)


@login_required(login_url='login')
def downvote_answer(request, question_id, answer_id):
    a = get_object_or_404(Answer, pk=answer_id)
    a.downvote(user=request.user.profile)
    return redirect('questions:question', pk=question_id)


@login_required(login_url='login')
def set_correct_answer(request, question_id, answer_id):
    q = get_object_or_404(Question, pk=question_id)
    a = get_object_or_404(Answer, pk=answer_id)
    if q.author.user.pk == request.user.pk:
        q.set_correct_answer(a)
        return redirect('questions:question', pk=question_id)
    return HttpResponseForbidden('Only author can choose the best answer')


def question_detail(request, pk: int):
    try:
        question = Question.objects.by_id(pk)
    except Question.DoesNotExist:
        raise Http404(f'Question #{pk} not found')

    paginator = Paginator(question.answers.all(), 20)
    trending = TopTrendingQuestionsMixin.get_trending()

    if request.method == 'POST' and request.user.is_authenticated:
        add_answer_form = AddAnswerForm(request.POST)
        if add_answer_form.is_valid():
            a = add_answer_form.save(commit=False)
            a.question = question
            a.author = request.user.profile
            a.created = timezone.now()
            a.save()
            messages.success(request, 'Your answer has been added')
        page_obj = paginator.get_page(1)
    else:
        add_answer_form = AddAnswerForm()
        page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'questions/question.html',
        {
            'question': question,
            'page_obj': page_obj,
            'is_paginated': page_obj.paginator.num_pages > 1,
            'add_answer_form': add_answer_form,
            TopTrendingQuestionsMixin.trending_ctx_name: trending
        }
    )


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

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q')
        if self.has_tag_prefix(query):
            return redirect(
                'questions:tag',
                tag_text=self.extract_query(query)
            )
        return super().get(self.request)

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
