from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Extend the existing User model using a one-to-one link
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    customergroup = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

# Signal to create or update User profile when User is created or saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
