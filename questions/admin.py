from django.contrib import admin

from .models import Question, Answer, Tag


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, dict(fields=['caption', 'text', 'tags', 'rating'])),
        ('Meta', dict(fields=['author', 'created'])),
    ]
    inlines = [AnswerInline]
    list_display = ['caption', 'text', 'author', 'rating', 'created']
    list_filter = ['created']
    search_fields = ['caption', 'text']


admin.site.register(Question, QuestionAdmin)
