from django.db import IntegrityError, models
from django.db.models import Q, QuerySet

from members.models import Member


class Tag(models.Model):
    text = models.CharField(max_length=20, unique=True)

    def __str__(self) -> str:
        return self.text


class QuestionManager(models.Manager):

    def n_trending(self, top_n: int) -> QuerySet:
        return self.order_by('-rating')[:top_n]

    def trending(self) -> QuerySet:
        return (
            self
            .order_by('-rating', '-created')
            .select_related('author')
            .prefetch_related('tags')
        )

    def recent(self) -> QuerySet:
        return (
            self
            .order_by('-created', '-rating')
            .select_related('author')
            .prefetch_related('tags')
        )

    def search_by_tag(self, query: str) -> QuerySet:
        try:
            tag = Tag.objects.get(text=query)
        except Tag.DoesNotExist:
            return Tag.objects.none()
        else:
            return (
                tag
                .questions
                .select_related('author')
                .prefetch_related('tags')
                .order_by('-rating', '-created')
            )

    def by_id(self, pk: int) -> 'Question':
        return (
            self
            .select_related('author')
            .prefetch_related('answers', 'answers__author', 'tags')
            .get(pk=pk)
        )

    def search_by_text(self, query: str) -> QuerySet:
        return (
            self
            .select_related('author')
            .prefetch_related('tags')
            .filter(Q(text__icontains=query) | Q(caption__icontains=query))
            .order_by('-rating', '-created')
        )


class Question(models.Model):
    caption = models.CharField(max_length=100)
    text = models.CharField(max_length=1000)
    author = models.ForeignKey(Member, on_delete=models.CASCADE)
    created = models.DateTimeField()
    tags = models.ManyToManyField(Tag, related_name='questions')
    rating = models.IntegerField(default=0)

    objects = QuestionManager()

    def __str__(self) -> str:
        return f'{self.author}: {self.caption}'

    def upvote(self, user) -> None:
        try:
            self.votes.create(user=user, question=self, up=True)
            self.rating += 1
            self.save()
        except IntegrityError:
            vote = self.votes.filter(user=user)
            if not vote[0].up:
                vote.update(up=True)
                self.rating += 2
                self.save()

    def downvote(self, user) -> None:
        try:
            self.votes.create(user=user, question=self, up=False)
            self.rating -= 1
            self.save()
        except IntegrityError:
            vote = self.votes.filter(user=user)
            if vote[0].up:
                vote.update(up=False)
                self.rating -= 2
                self.save()

    def set_correct_answer(self, answer) -> None:
        if answer.question == self:
            if hasattr(self, 'correct_answer'):
                if self.correct_answer.answer == answer:
                    correct = CorrectAnswer.objects.get(answer=answer)
                    correct.delete()
                else:
                    self.correct_answer.answer = answer
                    self.correct_answer.save()
            else:
                self.correct_answer = CorrectAnswer(
                    question=self,
                    answer=answer
                )
                self.correct_answer.save()


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    author = models.ForeignKey(Member, on_delete=models.CASCADE)
    text = models.CharField(max_length=1000)
    created = models.DateTimeField()
    rating = models.IntegerField(default=0)

    class Meta:
        ordering = ['-rating', '-created']

    def __str__(self) -> str:
        return f'{self.author}: {self.text}'

    def upvote(self, user) -> None:
        try:
            self.votes.create(user=user, answer=self, up=True)
            self.rating += 1
            self.save()
        except IntegrityError:
            vote = self.votes.filter(user=user)
            if not vote[0].up:
                vote.update(up=True)
                self.rating += 2
                self.save()

    def downvote(self, user) -> None:
        try:
            self.votes.create(user=user, answer=self, up=False)
            self.rating -= 1
            self.save()
        except IntegrityError:
            vote = self.votes.filter(user=user)
            if vote[0].up:
                vote.update(up=False)
                self.rating -= 2
                self.save()


class QuestionVote(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    up = models.BooleanField()

    class Meta:
        unique_together = ('user', 'question')


class AnswerVote(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE)
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    up = models.BooleanField()

    class Meta:
        unique_together = ('user', 'answer')


class CorrectAnswer(models.Model):
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name='correct_answer',
    )
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
