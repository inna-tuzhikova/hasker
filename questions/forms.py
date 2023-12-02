from django.core.exceptions import ValidationError
from django.forms import Field, ModelForm, Textarea

from .models import Answer, Question


class TagListField(Field):
    """Field for question tags"""
    LIST_SEP = ','
    MAX_TAGS_PER_FIELD = 3
    MAX_LENGTH = 20

    def to_python(self, value):
        if not value:
            return []
        return [v.strip() for v in value.strip().split(self.LIST_SEP)]

    def validate(self, value):
        super(TagListField, self).validate(value)
        if len(value) > self.MAX_TAGS_PER_FIELD:
            raise ValidationError(
                f'Maximum number of tags: {self.MAX_TAGS_PER_FIELD}'
            )
        for tag in value:
            if len(tag) > self.MAX_LENGTH:
                raise ValidationError(
                    f'Tag should be less than {self.MAX_LENGTH} characters'
                )
            if not tag:
                raise ValidationError('Tag should be non empty string')


class CreateQuestionForm(ModelForm):
    """Form with data for adding new question"""
    tag_list = TagListField()

    class Meta:
        model = Question
        fields = ['caption', 'text']
        widgets = dict(
            text=Textarea(attrs={'cols': 80, 'rows': 20})
        )


class AddAnswerForm(ModelForm):
    """Form with data for adding new answer"""
    class Meta:
        model = Answer
        fields = ['text']
        widgets = dict(
            text=Textarea(attrs={'cols': 80, 'rows': 10})
        )
