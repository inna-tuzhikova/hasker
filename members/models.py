from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Member(models.Model):
    user = models.OneToOneField(
        User,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars', null=True)

    def __str__(self) -> str:
        return self.user.__str__()


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs) -> None:
    if created:
        Member.objects.create(user=instance)
    instance.profile.save()
