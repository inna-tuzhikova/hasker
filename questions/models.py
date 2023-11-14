from django.db import models, IntegrityError


class User(models.Model):
    login = models.CharField(max_length=30)
    email = models.EmailField()
    password = models.CharField(max_length=30)
    registration_datetime = models.DateTimeField()
    avatar = models.CharField(max_length=2)

    def __str__(self):
        return self.login


class Tag(models.Model):
    text = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.text


class QuestionManager(models.Manager):
    def n_trending(self, top_n: int):
        return self.orderby('-rating')[:top_n]

    def trending(self):
        return self.orderby('-rating')

    def recent(self):
        return self.orderby('-created')

    def by_tag(self, query: str):
        return Tag.objects.get(text=query).questions


class Question(models.Model):
    caption = models.CharField(max_length=30)
    text = models.CharField(max_length=1000)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField()
    tags = models.ManyToManyField(Tag, related_name='questions')
    rating = models.IntegerField(default=0)

    objects = QuestionManager()

    def __str__(self):
        return f'{self.author}: {self.caption}'

    def upvote(self, user):
        try:
            self.votes.create(user=user, post=self, up=True)
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

    def down_vote(self, user):
        try:
            self.votes.create(user=user, post=self, up=False)
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
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=1000)
    created = models.DateTimeField()
    rating = models.IntegerField(default=0)
    correct = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.author}: {self.text}'

    def upvote(self, user):
        try:
            self.votes.create(user=user, post=self, up=True)
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

    def down_vote(self, user):
        try:
            self.votes.create(user=user, post=self, up=False)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    up = models.BooleanField()

    class Meta:
        unique_together = ('user', 'question')


class AnswerVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    up = models.BooleanField()

    class Meta:
        unique_together = ('user', 'answer')
