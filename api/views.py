from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from questions.models import Question
from questions.views import TagPrefixMixin
from .serializers import QuestionSerializer, AnswerSerializer


search_query = openapi.Parameter(
    'q',
    openapi.IN_QUERY,
    description='search query',
    type=openapi.TYPE_STRING
)
answers_page = openapi.Parameter(
    'page',
    openapi.IN_QUERY,
    description='question\'s answers page',
    type=openapi.TYPE_INTEGER
)


class QuestionViewSet(TagPrefixMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.recent()
    serializer_class = QuestionSerializer

    def maybe_paginated_response(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def trending(self, request):
        trending = Question.objects.trending()
        return self.maybe_paginated_response(trending)

    @action(detail=False)
    def top_trending(self, request):
        trending = Question.objects.n_trending(20)
        serializer = self.get_serializer(trending, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='get',
        operation_description='Questions answers',
        manual_parameters=[answers_page]
    )
    @action(detail=True, serializer_class=AnswerSerializer)
    def answers(self, request, *args, **kwargs):
        q = self.get_object()
        answers = q.answers.all()
        return self.maybe_paginated_response(answers)

    @swagger_auto_schema(
        method='get',
        operation_description='Search for text query',
        manual_parameters=[search_query],
    )
    @action(detail=False)
    def search(self, request, *args, **kwargs):
        query = request.query_params.get(search_query.name)
        if query is None:
            return Response(
                dict(error='Empty search query'),
                status=status.HTTP_400_BAD_REQUEST
            )
        if self.has_tag_prefix(query):
            tag = self.extract_query(query)
            search_results = Question.objects.search_by_tag(tag)
        else:
            search_results = Question.objects.search_by_text(query)
        return self.maybe_paginated_response(search_results)
