from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from members.models import Member

from .models import Answer, Question, Tag


def get_default_users():
    user = User.objects.create_user(
        username='test_user',
        email='test@example.com',
        password='test_password'
    )
    second_user = User.objects.create_user(
        username='second_test_user',
        email='second_test@example.com',
        password='second_test_password'
    )
    member = Member(user=user)
    member.save()
    second_member = Member(user=second_user)
    second_member.save()
    return user, second_user, member, second_member


def get_default_question(member, **fields):
    default_fields = dict(
        caption='Test',
        text='Test',
        author=member,
        created=timezone.now(),
    )
    default_fields.update(fields)
    return Question.objects.create(**default_fields)


def get_default_answer(question, author, **fields):
    default_fields = dict(
        question=question,
        author=author,
        text='Test',
        created=timezone.now()
    )
    default_fields.update(fields)
    return Answer.objects.create(**default_fields)


class TagModelTests(TestCase):
    def test_add_correct_tag(self):
        Tag.objects.create(text='tag 1')

    def test_add_invalid_tag(self):
        with self.assertRaises(ValidationError):
            t = Tag(text='a' * 21)
            t.full_clean()
            t.save()

    def test_add_duplicate_tags(self):
        with self.assertRaises(IntegrityError):
            Tag.objects.create(text='tag 1')
            Tag.objects.create(text='tag 1')


class QuestionModelTests(TestCase):
    def setUp(self):
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()

    def test_add_correct_question(self):
        get_default_question(self.member)

    def test_add_invalid_question(self):
        with self.assertRaises(ValidationError):
            q = Question(
                caption='T' * 101,
                text='Test',
                author=self.member,
                created=timezone.now(),
            )
            q.full_clean()
            q.save()
        with self.assertRaises(ValidationError):
            q = Question(
                caption='Test',
                text='T' * 1001,
                author=self.member,
                created=timezone.now(),
            )
            q.full_clean()
            q.save()

    def test_n_trending(self):
        for idx in range(10):
            get_default_question(self.member, rating=idx)
        result = Question.objects.n_trending(top_n=5)
        self.assertEqual(result.count(), 5)
        self.assertEqual(result[0].rating, 9)
        self.assertEqual(result[4].rating, 5)

    def test_trending(self):
        for idx in range(10):
            get_default_question(self.member, rating=idx)
        result = Question.objects.trending()
        self.assertEqual(result.count(), 10)
        self.assertEqual(result[0].rating, 9)
        self.assertEqual(result[1].rating, 8)
        self.assertEqual(result[9].rating, 0)

    def test_recent(self):
        recent = timezone.now()
        for idx in range(10):
            get_default_question(
                self.member, created=recent - timedelta(days=idx)
            )
        result = Question.objects.recent()
        self.assertEqual(result.count(), 10)
        self.assertEqual(result[0].created, recent)
        self.assertEqual(result[1].created, recent - timedelta(days=1))
        self.assertEqual(result[9].created, recent - timedelta(days=9))

    def test_search_by_tag(self):
        tag_1 = Tag.objects.create(text='tag 1')
        tag_2 = Tag.objects.create(text='tag 2')
        for _ in range(10):
            q = get_default_question(self.member)
            q.tags.add(tag_1)
        for _ in range(5):
            q = get_default_question(self.member)
            q.tags.add(tag_2)
        tag_1_search_result = Question.objects.search_by_tag('tag 1')
        tag_2_search_result = Question.objects.search_by_tag('tag 2')
        self.assertEqual(tag_1_search_result.count(), 10)
        self.assertEqual(tag_2_search_result.count(), 5)

    def test_search_by_query(self):
        for _ in range(10):
            get_default_question(self.member, caption='query_0', text='query_1')
        for _ in range(5):
            get_default_question(self.member, caption='query_2', text='query_0')
        result = Question.objects.search_by_text('Query_0')
        self.assertEqual(result.count(), 15)
        result = Question.objects.search_by_text('Query_1')
        self.assertEqual(result.count(), 10)
        result = Question.objects.search_by_text('query_2')
        self.assertEqual(result.count(), 5)

    def test_question_upvote(self):
        q = get_default_question(self.member)
        self.assertEqual(q.rating, 0)
        q.upvote(self.second_member)
        self.assertEqual(q.rating, 1)

    def test_question_upvote_twice(self):
        q = get_default_question(self.member)
        self.assertEqual(q.rating, 0)
        q.upvote(self.second_member)
        q.upvote(self.member)
        self.assertEqual(q.rating, 2)

    def test_question_downvote(self):
        q = get_default_question(self.member)
        self.assertEqual(q.rating, 0)
        q.downvote(self.second_member)
        self.assertEqual(q.rating, -1)

    def test_question_downvote_twice(self):
        q = get_default_question(self.member)
        self.assertEqual(q.rating, 0)
        q.downvote(self.second_member)
        q.downvote(self.member)
        self.assertEqual(q.rating, -2)

    def test_question_up_down_vote(self):
        q = get_default_question(self.member)
        self.assertEqual(q.rating, 0)
        q.downvote(self.second_member)
        q.upvote(self.member)
        self.assertEqual(q.rating, 0)

    def test_set_invalid_answer_as_correct(self):
        q_1 = get_default_question(self.member)
        a_1 = get_default_answer(q_1, self.second_member)
        q_2 = get_default_question(self.member)
        q_2.set_correct_answer(a_1)
        exc = Question.correct_answer.RelatedObjectDoesNotExist
        with self.assertRaises(exc):
            print(q_2.correct_answer)

    def test_set_first_correct_answer(self):
        q = get_default_question(self.member)
        a = get_default_answer(q, self.second_member)
        q.set_correct_answer(a)
        self.assertEqual(q.correct_answer.answer, a)

    def test_toggle_correct_answer(self):
        q = get_default_question(self.member)
        a = get_default_answer(q, self.second_member)
        q.set_correct_answer(a)
        self.assertEqual(q.correct_answer.answer, a)
        q.set_correct_answer(a)

        q = Question.objects.get(pk=q.pk)
        exc = Question.correct_answer.RelatedObjectDoesNotExist
        with self.assertRaises(exc):
            print(q.correct_answer)

    def test_change_correct_answer(self):
        q = get_default_question(self.member)
        a_1 = get_default_answer(q, self.second_member)
        a_2 = get_default_answer(q, self.second_member)
        q.set_correct_answer(a_1)
        self.assertEqual(q.correct_answer.answer, a_1)

        q.set_correct_answer(a_2)
        self.assertEqual(q.correct_answer.answer, a_2)


class AnswerModelTests(TestCase):
    def setUp(self):
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.question = get_default_question(self.member)
        self.answer = get_default_answer(self.question, self.second_member)

    def test_add_correct_answer(self):
        get_default_answer(self.question, self.second_member)

    def test_add_invalid_answer(self):
        with self.assertRaises((ValidationError, DataError)):
            a = get_default_answer(
                self.question, self.second_member, text='T' * 1001
            )
            a.full_clean()
            a.save()

    def test_answer_upvote(self):
        self.assertEqual(self.answer.rating, 0)
        self.answer.upvote(self.member)
        self.assertEqual(self.answer.rating, 1)

    def test_answer_upvote_twice(self):
        self.assertEqual(self.answer.rating, 0)
        self.answer.upvote(self.member)
        self.assertEqual(self.answer.rating, 1)
        self.answer.upvote(self.second_member)
        self.assertEqual(self.answer.rating, 2)

    def test_answer_downvote(self):
        self.assertEqual(self.answer.rating, 0)
        self.answer.downvote(self.member)
        self.assertEqual(self.answer.rating, -1)

    def test_answer_downvote_twice(self):
        self.assertEqual(self.answer.rating, 0)
        self.answer.downvote(self.member)
        self.assertEqual(self.answer.rating, -1)
        self.answer.downvote(self.second_member)
        self.assertEqual(self.answer.rating, -2)

    def test_answer_up_down_vote(self):
        self.assertEqual(self.answer.rating, 0)
        self.answer.upvote(self.member)
        self.assertEqual(self.answer.rating, 1)
        self.answer.downvote(self.second_member)
        self.assertEqual(self.answer.rating, 0)


class IndexRecentViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()

    def test_not_authorized_user(self):
        response = self.client.get(reverse('questions:index'))
        self.assertEqual(response.status_code, 200)

    def test_no_questions(self):
        response = self.client.get(reverse('questions:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort_type'], 'recent')
        self.assertQuerySetEqual(response.context['questions'], [])

    def test_valid_sort(self):
        recent = timezone.now()
        for idx in range(10, -1, -1):
            get_default_question(
                self.member,
                created=recent - timedelta(days=idx)
            )
        response = self.client.get(reverse('questions:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort_type'], 'recent')
        result = response.context['questions']
        self.assertEqual(result[0].created, recent)
        self.assertEqual(result[1].created, recent - timedelta(days=1))

    def test_pagination(self):
        for _ in range(25):
            get_default_question(self.member)
        response = self.client.get(reverse('questions:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort_type'], 'recent')
        self.assertEqual(response.context['questions'].count(), 20)
        response = self.client.get(
            reverse('questions:index'),
            dict(page=2)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort_type'], 'recent')
        self.assertEqual(response.context['questions'].count(), 5)


class IndexTrendingViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()

    def test_not_authorized_user(self):
        response = self.client.get(reverse('questions:index_trending'))
        self.assertEqual(response.status_code, 200)

    def test_no_questions(self):
        response = self.client.get(reverse('questions:index_trending'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort_type'], 'trending')
        self.assertQuerySetEqual(response.context['questions'], [])

    def test_valid_sort(self):
        for idx in range(10, -1, -1):
            get_default_question(self.member, rating=idx)
        response = self.client.get(reverse('questions:index_trending'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort_type'], 'trending')
        result = response.context['questions']
        self.assertEqual(result[0].rating, 10)
        self.assertEqual(result[1].rating, 9)
        self.assertEqual(result[10].rating, 0)

    def test_pagination(self):
        for _ in range(25):
            get_default_question(self.member)
        response = self.client.get(reverse('questions:index_trending'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort_type'], 'trending')
        self.assertEqual(response.context['questions'].count(), 20)
        response = self.client.get(
            reverse('questions:index_trending'),
            dict(page=2)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort_type'], 'trending')
        self.assertEqual(response.context['questions'].count(), 5)


class AskQuestionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse('questions:ask'))
        self.assertEqual(response.status_code, 302)

    def test_invalid_question(self):
        response = self.client.post(
            reverse('questions:ask'),
            dict(
                caption='T' * 101,
                text='Test',
                tag_list='a,b,c'
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)

    def test_no_tags_in_question(self):
        response = self.client.post(
            reverse('questions:ask'),
            dict(
                caption='Test',
                text='Test',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)

    def test_empty_tags_in_question(self):
        response = self.client.post(
            reverse('questions:ask'),
            dict(
                caption='Test',
                text='Test',
                tag_list=''
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)

    def test_too_many_tags_in_question(self):
        response = self.client.post(
            reverse('questions:ask'),
            dict(
                caption='Test',
                text='Test',
                tag_list='a,b,c,d'
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)

    def test_valid_question(self):
        response = self.client.post(
            reverse('questions:ask'),
            dict(
                caption='Test',
                text='Test',
                tag_list='a,b,c'
            )
        )
        self.assertEqual(response.status_code, 302)


class UpvoteQuestionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        self.question = get_default_question(self.second_member)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.post(reverse(
            'questions:upvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, 0)

    def test_upvote_unknown_question(self):
        response = self.client.get(reverse(
            'questions:upvote_question',
            kwargs=dict(pk=666)
        ))
        self.assertEqual(response.status_code, 404)

    def test_question_upvote(self):
        response = self.client.get(reverse(
            'questions:upvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, 1)

    def test_question_upvote_twice(self):
        response = self.client.get(reverse(
            'questions:upvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, 1)

        self.client.logout()
        self.client.force_login(self.second_user)
        response = self.client.get(reverse(
            'questions:upvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, 2)

    def test_question_up_down_vote(self):
        response = self.client.get(reverse(
            'questions:upvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, 1)

        self.client.logout()
        self.client.force_login(self.second_user)
        response = self.client.get(reverse(
            'questions:downvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, 0)


class DownvoteQuestionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        self.question = get_default_question(self.second_member)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.post(reverse(
            'questions:downvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, 0)

    def test_downvote_unknown_question(self):
        response = self.client.get(reverse(
            'questions:downvote_question',
            kwargs=dict(pk=666)
        ))
        self.assertEqual(response.status_code, 404)

    def test_question_downvote(self):
        response = self.client.get(reverse(
            'questions:downvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, -1)

    def test_question_downvote_twice(self):
        response = self.client.get(reverse(
            'questions:downvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, -1)

        self.client.logout()
        self.client.force_login(self.second_user)
        response = self.client.get(reverse(
            'questions:downvote_question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, -2)


class UpvoteAnswerViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        self.question = get_default_question(self.member)
        self.answer = get_default_answer(self.question, self.second_member)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse(
            'questions:upvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 0)

    def test_upvote_unknown_answer(self):
        response = self.client.get(reverse(
            'questions:upvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=666
            )
        ))
        self.assertEqual(response.status_code, 404)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 0)

    def test_answer_upvote(self):
        response = self.client.get(reverse(
            'questions:upvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 1)

    def test_answer_upvote_twice(self):
        response = self.client.get(reverse(
            'questions:upvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 1)

        self.client.logout()
        self.client.force_login(self.second_user)
        response = self.client.get(reverse(
            'questions:upvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 2)

    def test_answer_up_down_vote(self):
        response = self.client.get(reverse(
            'questions:upvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 1)

        self.client.logout()
        self.client.force_login(self.second_user)
        response = self.client.get(reverse(
            'questions:downvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 0)


class DownvoteAnswerViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        self.question = get_default_question(self.member)
        self.answer = get_default_answer(self.question, self.second_member)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse(
            'questions:downvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 0)

    def test_downvote_unknown_answer(self):
        response = self.client.get(reverse(
            'questions:downvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=666
            )
        ))
        self.assertEqual(response.status_code, 404)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 0)

    def test_answer_downvote(self):
        response = self.client.get(reverse(
            'questions:downvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, -1)

    def test_answer_downvote_twice(self):
        response = self.client.get(reverse(
            'questions:downvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, -1)

        self.client.logout()
        self.client.force_login(self.second_user)
        response = self.client.get(reverse(
            'questions:downvote_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, -2)


class SetCorrectAnswerViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        self.question = get_default_question(self.member)
        self.answer = get_default_answer(self.question, self.second_member)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk,
            )
        ))
        self.assertEqual(response.status_code, 302)
        exc = Question.correct_answer.RelatedObjectDoesNotExist
        with self.assertRaises(exc):
            print(self.question.correct_answer)

    def test_unknown_question(self):
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=666,
                answer_id=self.answer.pk,
            )
        ))
        self.assertEqual(response.status_code, 404)
        exc = Question.correct_answer.RelatedObjectDoesNotExist
        with self.assertRaises(exc):
            print(self.question.correct_answer)

    def test_unknown_answer(self):
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=666,
            )
        ))
        self.assertEqual(response.status_code, 404)
        exc = Question.correct_answer.RelatedObjectDoesNotExist
        with self.assertRaises(exc):
            print(self.question.correct_answer)

    def test_mismatched_question_and_answer(self):
        new_question = get_default_question(self.member)
        new_answer = get_default_answer(new_question, self.second_member)
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=new_answer.pk,
            )
        ))
        self.assertEqual(response.status_code, 302)
        exc = Question.correct_answer.RelatedObjectDoesNotExist
        with self.assertRaises(exc):
            print(self.question.correct_answer)

    def test_set_by_question_author(self):
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk,
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.question.correct_answer.answer, self.answer)

    def test_set_correct_by_non_question_author(self):
        self.client.logout()
        self.client.force_login(self.second_user)
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk,
            )
        ))
        self.assertEqual(response.status_code, 403)
        exc = Question.correct_answer.RelatedObjectDoesNotExist
        with self.assertRaises(exc):
            print(self.question.correct_answer)

    def test_toggle_best_answer(self):
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk,
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.question.correct_answer.answer, self.answer)

        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk,
            )
        ))
        self.question.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        exc = Question.correct_answer.RelatedObjectDoesNotExist
        with self.assertRaises(exc):
            print(self.question.correct_answer)

    def test_change_best_answer(self):
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=self.answer.pk,
            )
        ))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.question.correct_answer.answer, self.answer)

        new_answer = get_default_answer(self.question, self.second_member)
        response = self.client.get(reverse(
            'questions:set_correct_answer',
            kwargs=dict(
                question_id=self.question.pk,
                answer_id=new_answer.pk,
            )
        ))
        self.question.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.question.correct_answer.answer, new_answer)


class QuestionDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        self.question = get_default_question(self.member)
        self.answer = get_default_answer(self.question, self.second_member)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse(
            'questions:question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 200)

    def test_unknown_question(self):
        response = self.client.get(reverse(
            'questions:question',
            kwargs=dict(pk=666)
        ))
        self.assertEqual(response.status_code, 404)

    def test_question_with_answers(self):
        response = self.client.get(reverse(
            'questions:question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question'].pk, self.question.pk)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_question_without_answers(self):
        q = get_default_question(self.member)
        response = self.client.get(reverse(
            'questions:question',
            kwargs=dict(pk=q.pk)
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question'].pk, q.pk)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_new_invalid_answer(self):
        response = self.client.post(
            reverse(
                'questions:question',
                kwargs=dict(pk=self.question.pk)
            ),
            dict(
                text='T' * 1001
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['add_answer_form'].errors)
        self.assertEqual(self.question.answers.count(), 1)

    def test_new_valid_answer(self):
        response = self.client.post(
            reverse(
                'questions:question',
                kwargs=dict(pk=self.question.pk)
            ),
            dict(
                text='Test'
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.question.answers.count(), 2)

    def test_email_on_new_answer(self):
        response = self.client.post(
            reverse(
                'questions:question',
                kwargs=dict(pk=self.question.pk)
            ),
            dict(
                text='Test'
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mail.outbox[0].to[0], self.question.author.user.email)

    def test_pagination(self):
        for _ in range(31):
            get_default_answer(self.question, self.second_member)

        response = self.client.get(reverse(
            'questions:question',
            kwargs=dict(pk=self.question.pk)
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 30)

        response = self.client.get(
            reverse(
                'questions:question',
                kwargs=dict(pk=self.question.pk)
            ),
            dict(page=2)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 2)


class SearchByQueryViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        self.questions = [
            get_default_question(self.member, text='q1', caption='q2'),
            get_default_question(self.member, text='q2', caption='q1'),
            get_default_question(self.member, text='q3', caption='q3'),
            get_default_question(self.member, text='q4', caption='q5'),
            get_default_question(self.member, text='q1', caption='q3'),
        ]

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(
            reverse('questions:search'),
            dict(q='q')
        )
        self.assertEqual(response.status_code, 200)

    def test_tag_query(self):
        response = self.client.get(reverse('questions:search'), dict(q='tag:a'))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('questions:search'), dict(q='tag:b'))
        self.assertEqual(response.status_code, 302)

    def test_existent_query(self):
        response = self.client.get(reverse('questions:search'), dict(q='q1'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 3)

        response = self.client.get(reverse('questions:search'), dict(q='q2'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 2)

        response = self.client.get(reverse('questions:search'), dict(q='q3'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 2)

        response = self.client.get(reverse('questions:search'), dict(q='q4'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 1)

        response = self.client.get(reverse('questions:search'), dict(q='q5'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 1)

    def test_non_existent_query(self):
        response = self.client.get(reverse('questions:search'), dict(q='q6'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 0)

        response = self.client.get(reverse('questions:search'), dict(q='q7'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 0)

        response = self.client.get(reverse('questions:search'), dict(q='q8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 0)

    def test_pagination(self):
        for _ in range(47):
            get_default_question(self.member, text='q6')

        response = self.client.get(
            reverse('questions:search'),
            dict(q='q6')
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 20)

        response = self.client.get(
            reverse('questions:search'),
            dict(q='q6', page=2)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 20)
        response = self.client.get(
            reverse('questions:search'),
            dict(q='q6', page=3)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 7)


class SearchByTagViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)

        self.tag_1 = Tag.objects.create(text='tag_1')
        self.tag_2 = Tag.objects.create(text='tag_2')
        for _ in range(10):
            q = get_default_question(self.member)
            q.tags.add(self.tag_1)
        for _ in range(5):
            q = get_default_question(self.member)
            q.tags.add(self.tag_2)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse(
            'questions:tag',
            kwargs=dict(tag_text='tag_1')
        ))
        self.assertEqual(response.status_code, 200)

    def test_search_existent_tag(self):
        response = self.client.get(reverse(
            'questions:tag',
            kwargs=dict(tag_text='tag_1')
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 10)

        response = self.client.get(reverse(
            'questions:tag',
            kwargs=dict(tag_text='tag_2')
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 5)

    def test_search_non_existent_tag(self):
        response = self.client.get(reverse(
            'questions:tag',
            kwargs=dict(tag_text='tag_3')
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 0)

    def test_pagination(self):
        for _ in range(22):
            q = get_default_question(self.member)
            q.tags.add(self.tag_1)

        response = self.client.get(
            reverse('questions:tag', kwargs=dict(tag_text='tag_1')),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 20)

        response = self.client.get(
            reverse('questions:tag', kwargs=dict(tag_text='tag_1')),
            dict(page=2)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].count(), 12)
