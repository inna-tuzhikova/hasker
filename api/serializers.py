from rest_framework import serializers

from questions.models import Answer, Question, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    class Meta:
        model = Tag
        fields = ('text',)


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question model"""
    author = serializers.ReadOnlyField(source='author.user.username')
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        model = Question
        fields = ('caption', 'text', 'author', 'created', 'tags', 'rating')


class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for Answer model"""
    question = serializers.ReadOnlyField(source='question.caption')
    author = serializers.ReadOnlyField(source='author.user.username')

    class Meta:
        model = Answer
        fields = ('question', 'author', 'text', 'created', 'rating')
