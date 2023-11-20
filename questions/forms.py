from django.forms import ModelForm, Field, Textarea
from django.core.exceptions import ValidationError

from .models import Question


class TagListField(Field):
    LIST_SEP = ','

    def to_python(self, value):
        if not value:
            return []
        return [v.strip() for v in value.strip().split(self.LIST_SEP)]

    def validate(self, value):
        super(TagListField, self).validate(value)
        for tag in value:
            if not tag:
                raise ValidationError('Tag should be non empty string')


class CreateQuestionForm(ModelForm):
    tag_list = TagListField()

    class Meta:
        model = Question
        fields = ['caption', 'text']
        widgets = dict(
            text=Textarea(attrs={'cols': 80, 'rows': 20})
        )
