from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from questions.models import Question
from .serializers import QuestionSerializer, AnswerSerializer


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.recent()
    serializer_class = QuestionSerializer

    @action(detail=False)
    def trending(self, request):
        trending = Question.objects.trending()
        page = self.paginate_queryset(trending)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(trending, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def top_trending(self, request):
        trending = Question.objects.n_trending(20)
        serializer = self.get_serializer(trending, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def answers(self, request, *args, **kwargs):
        q = self.get_object()
        answers = q.answers.all()
        page = self.paginate_queryset(answers)
        if page is not None:
            serializer = AnswerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = AnswerSerializer(answers, many=True)
        return Response(serializer.data)
