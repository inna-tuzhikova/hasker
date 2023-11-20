from django.db import IntegrityError, models
from django.db.models import Q

from members.models import Member


class Tag(models.Model):
    text = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.text


class QuestionManager(models.Manager):
    def n_trending(self, top_n: int):
        return self.order_by('-rating')[:top_n]

    def trending(self):
        return (
            self
            .order_by('-rating', '-created')
            .select_related('author')
            .prefetch_related('tags')
        )

    def recent(self):
        return (
            self
            .order_by('-created', '-rating')
            .select_related('author')
            .prefetch_related('tags')
        )

    def by_tag(self, query: str):
        return Tag.objects.get(text=query).questions

    def by_id(self, pk: int):
        return (
            self
            .select_related('author')
            .prefetch_related('answers', 'answers__author', 'tags')
            .get(pk=pk)
        )

    def search_by_text(self, query: str):
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

    def __str__(self):
        return f'{self.author}: {self.caption}'

    def upvote(self, user):
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
            else:
                return 'already_up_voted'
        return 'ok'

    def downvote(self, user):
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
            else:
                return 'already_down_voted'
        return 'ok'


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
    correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['-rating', '-created']

    def __str__(self):
        return f'{self.author}: {self.text}'

    def upvote(self, user):
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
            else:
                return 'already_up_voted'
        return 'ok'

    def downvote(self, user):
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
            else:
                return 'already_down_voted'
        return 'ok'


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
