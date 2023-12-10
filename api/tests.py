from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from members.models import Member
from questions.models import Answer, Question, Tag


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


class RecentQuestionsTests(APITestCase):
    def setUp(self):
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        self.recent_date = timezone.now()
        for idx in range(50):
            get_default_question(
                self.member,
                created=self.recent_date - timedelta(days=idx)
            )

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse('api:questions-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_questions(self):
        Question.objects.all().delete()
        response = self.client.get(reverse('api:questions-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_recent_questions(self):
        response = self.client.get(reverse('api:questions-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        to_repr = serializers.DateTimeField().to_representation
        search_results = response.data['results']
        self.assertEqual(
            search_results[0]['created'],
            to_repr(self.recent_date)
        )
        self.assertEqual(
            search_results[5]['created'],
            to_repr(self.recent_date - timedelta(days=5))
        )

    def test_pagination(self):
        response = self.client.get(reverse('api:questions-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 20)

        response = self.client.get(reverse('api:questions-list'), dict(page=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 20)

        response = self.client.get(reverse('api:questions-list'), dict(page=3))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 10)


class TrendingQuestionsTests(APITestCase):
    def setUp(self):
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)
        for idx in range(49):
            get_default_question(self.member, rating=idx)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse('api:questions-trending'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_questions(self):
        Question.objects.all().delete()
        response = self.client.get(reverse('api:questions-trending'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_trending_questions(self):
        response = self.client.get(reverse('api:questions-trending'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(search_results[0]['rating'], 48)
        self.assertEqual(search_results[5]['rating'], 43)

    def test_pagination(self):
        response = self.client.get(reverse('api:questions-trending'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 20)

        response = self.client.get(
            reverse('api:questions-trending'),
            dict(page=2)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 20)

        response = self.client.get(
            reverse('api:questions-trending'),
            dict(page=3)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 9)


class TopTrendingQuestionsTests(APITestCase):
    def setUp(self):
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse('api:questions-top-trending'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_questions(self):
        response = self.client.get(reverse('api:questions-top-trending'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_few_questions(self):
        Question.objects.all().delete()
        for idx in range(12):
            get_default_question(self.member, rating=idx)

        response = self.client.get(reverse('api:questions-top-trending'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 12)
        self.assertEqual(response.data[0]['rating'], 11)
        self.assertEqual(response.data[5]['rating'], 6)

    def test_top_trending_questions(self):
        for idx in range(37):
            get_default_question(self.member, rating=idx)

        response = self.client.get(reverse('api:questions-top-trending'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 20)
        self.assertEqual(response.data[0]['rating'], 36)
        self.assertEqual(response.data[5]['rating'], 31)


class QuestionDetailTests(APITestCase):
    def setUp(self):
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
            'api:questions-detail',
            kwargs=dict(pk=1)
        ))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_existent_question(self):
        response = self.client.get(reverse(
            'api:questions-detail',
            kwargs=dict(pk=12)
        ))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_question_details(self):
        response = self.client.get(reverse(
            'api:questions-detail',
            kwargs=dict(pk=self.question.id)
        ))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['caption'], 'Test')
        self.assertEqual(response.data['text'], 'Test')
        self.assertEqual(response.data['author'], self.member.user.username)

    def test_question_with_no_answers(self):
        q = get_default_question(self.member)
        response = self.client.get(reverse(
            'api:questions-answers',
            kwargs=dict(pk=q.id)
        ))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_question_with_answers(self):
        for idx in range(10):
            get_default_answer(self.question, self.second_member, rating=idx)
        response = self.client.get(reverse(
            'api:questions-answers',
            kwargs=dict(pk=self.question.id)
        ))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 11)
        self.assertEqual(response.data['results'][0]['rating'], 9)
        self.assertEqual(response.data['results'][7]['rating'], 2)

    def test_answers_pagination(self):
        for idx in range(25):
            get_default_answer(self.question, self.second_member)

        response = self.client.get(reverse(
            'api:questions-answers',
            kwargs=dict(pk=self.question.id)
        ))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 20)

        response = self.client.get(
            reverse(
                'api:questions-answers',
                kwargs=dict(
                    pk=self.question.id
                )
            ),
            dict(page=2)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 6)


class SearchQuestionsTests(APITestCase):
    def setUp(self):
        (
            self.user, self.second_user,
            self.member, self.second_member
        ) = get_default_users()
        self.client.force_login(self.user)

    def test_not_authorized_user(self):
        self.client.logout()
        response = self.client.get(reverse('api:questions-search'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_search_query(self):
        response = self.client.get(reverse('api:questions-search'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_text(self):
        for idx in range(5):
            get_default_question(self.member, caption='Q1', text='Q2')
        for idx in range(6):
            get_default_question(self.member, caption='Q2', text='Q2')
        for idx in range(7):
            get_default_question(self.member, caption='Q3', text='Q1')
        for idx in range(8):
            get_default_question(self.member, caption='Q3', text='Q2')

        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='q1')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 12)

        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='q2')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 19)

        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='q3')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 15)

    def test_search_by_non_existent_text(self):
        for idx in range(5):
            get_default_question(self.member)
        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='not exist')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_search_by_tag(self):
        tag_1 = Tag.objects.create(text='tag_1')
        tag_2 = Tag.objects.create(text='tag_2')
        for idx in range(5):
            q = get_default_question(self.member)
            q.tags.add(tag_1)
            q.save()
        for idx in range(10):
            q = get_default_question(self.member)
            q.tags.add(tag_2)
            q.save()

        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='tag:tag_1')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='tag:tag_2')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def search_by_non_existent_tag(self):
        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='tag:no_existent_tag')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_pagination(self):
        for idx in range(31):
            get_default_question(self.member, caption='Q1')
        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='q1')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 20)

        response = self.client.get(
            reverse('api:questions-search'),
            dict(q='q1', page=2)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search_results = response.data['results']
        self.assertEqual(len(search_results), 11)
