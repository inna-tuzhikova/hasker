from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from questions.models import Question
from questions.views import TagPrefixMixin

from .serializers import AnswerSerializer, QuestionSerializer

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
    """Set of views responsible for question resource

    Endpoints:
     - question list, sorted by creation date
     - question list, sorted by rating
     - top 20 trending questions
     - question details
     - question answers
     - search by text and tag
    """
    queryset = Question.objects.recent()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def maybe_paginated_response(self, queryset):
        """Packs queryset in paginated output"""
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def trending(self, request):
        """Action returning paginated list of questions sorted by rating"""
        trending = Question.objects.trending()
        return self.maybe_paginated_response(trending)

    @action(detail=False)
    def top_trending(self, request):
        """Action returning top 20 the most rated questions"""
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
        """Action returning paginated question answers"""
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
        """Action returning search results for text ang tag query"""
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
