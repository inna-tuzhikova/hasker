from typing import Callable, Optional

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.forms import Form
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.base import ContextMixin, View
from django.views.generic.edit import CreateView

from members.models import Member

from .forms import AddAnswerForm, CreateQuestionForm
from .models import Answer, Question, Tag


class TopTrendingQuestionsMixin:
    """Mixin to add information about most rated questions"""
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
    """Base class for index pages"""
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
    """Index page with recent sort type"""
    sort_type = 'recent'

    def get_queryset(self):
        return Question.objects.recent()


class IndexTrendingView(IndexView):
    """Index page with trending sort type"""
    sort_type = 'trending'

    def get_queryset(self):
        return Question.objects.trending()


class AskQuestionView(
    TopTrendingQuestionsMixin,
    LoginRequiredMixin,
    CreateView
):
    """View to add new question"""
    model = Question
    form_class = CreateQuestionForm
    template_name = 'questions/ask.html'
    login_url = 'login'

    def form_valid(self, form: Form):
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


class QuestionVoteView(LoginRequiredMixin, View):
    """Base for questions votes"""
    login_url = 'login'

    def post(self, request, pk: int):
        q = get_object_or_404(Question, pk=pk)
        self.get_voter(q)(request.user.profile)
        return redirect('questions:question', pk=pk)

    def get_voter(self, question: Question) -> Callable[[Member], None]:
        """Returns method for specific vote action by specified user"""
        raise NotImplementedError


class UpvoteQuestionView(QuestionVoteView):
    """Increments question's rating"""
    def get_voter(self, question: Question) -> Callable[[Member], None]:
        return question.upvote


class DownvoteQuestionView(QuestionVoteView):
    """Decrements question's rating"""
    def get_voter(self, question: Question) -> Callable[[Member], None]:
        return question.downvote


class AnswerVoteView(LoginRequiredMixin, View):
    """Base for answers votes"""
    login_url = 'login'

    def post(self, request, question_id: int, answer_id: int):
        a = get_object_or_404(Answer, pk=answer_id)
        self.get_voter(a)(request.user.profile)
        return redirect('questions:question', pk=question_id)

    def get_voter(self, answer: Answer) -> Callable[[Member], None]:
        """Returns method for specific vote action by specified user"""
        raise NotImplementedError


class UpvoteAnswerView(AnswerVoteView):
    """Increments answer's rating"""
    def get_voter(self, answer: Answer) -> Callable[[Member], None]:
        return answer.upvote


class DownvoteAnswerView(AnswerVoteView):
    """Decrements answer's rating"""
    def get_voter(self, answer: Answer) -> Callable[[Member], None]:
        return answer.downvote


class SetCorrectAnswerView(LoginRequiredMixin, View):
    """Allows question's author to choose the best answer"""
    login_url = 'login'

    def post(self, request, question_id: int, answer_id: int):
        q = get_object_or_404(Question, pk=question_id)
        a = get_object_or_404(Answer, pk=answer_id)
        if q.author.user.pk == request.user.pk:
            q.set_correct_answer(a)
            return redirect('questions:question', pk=question_id)
        return HttpResponseForbidden('Only author can choose the best answer')


class QuestionDetailView(TopTrendingQuestionsMixin, ContextMixin, View):
    """Question and its answers"""
    template_name = 'questions/question.html'

    def get(
        self,
        request,
        pk: int,
        question: Question | None = None,
        add_answer_form: AddAnswerForm | None = None
    ):
        question = question or get_object_or_404(Question, pk=pk)
        paginator = Paginator(question.answers.all(), 30)
        page_obj = paginator.get_page(request.GET.get('page'))
        add_answer_form = add_answer_form or AddAnswerForm()
        context = super().get_context_data(
            question=question,
            page_obj=page_obj,
            is_paginated=page_obj.paginator.num_pages > 1,
            add_answer_form=add_answer_form,
        )
        return render(
            request,
            self.template_name,
            context
        )

    def post(self, request, pk: int):
        question = get_object_or_404(Question, pk=pk)
        add_answer_form = AddAnswerForm(request.POST)
        if request.user.is_authenticated and add_answer_form.is_valid():
            a = add_answer_form.save(commit=False)
            a.question = question
            a.author = request.user.profile
            a.created = timezone.now()
            a.save()
            messages.success(request, 'Your answer has been added')
            notify_on_new_answer(request=request, question_id=pk)
            return redirect('questions:question', pk=pk)
        return self.get(request, pk, question, add_answer_form)


def notify_on_new_answer(request, question_id: int):
    """Sends email to question author when new answer is posted"""
    ctx = dict(
        username=request.user.username,
        question_url=request.build_absolute_uri(
            reverse('questions:question', kwargs=dict(pk=question_id))
        )
    )
    html_body = render_to_string('questions/new_answer_email.html', ctx)
    msg = EmailMultiAlternatives(
        subject='New answer',
        body='',
        from_email=None,
        to=[request.user.email]
    )
    msg.attach_alternative(html_body, 'text/html')
    msg.send(fail_silently=False)


class TagPrefixMixin:
    """Helper to process search tag notation"""
    tag_prefix = 'tag:'

    def has_tag_prefix(self, query: str):
        return query.startswith(self.tag_prefix)

    def extract_query(self, query: str):
        return query[len(self.tag_prefix):]

    def with_tag_prefix(self, query: str):
        return self.tag_prefix + query


class SearchByQueryView(TagPrefixMixin, TopTrendingQuestionsMixin, ListView):
    """View to search questions by text query"""
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
    """View to search questions by tag text"""
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
