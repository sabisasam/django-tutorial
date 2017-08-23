import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django_extensions.management.signals import post_command
from django_extensions.management.commands.update_permissions import Command as UpdatePermissionsCommand


class Question(TimeStampedModel):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    
    def __str__(self):
        return self.question_text
    
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

    class Meta:
        permissions = (
            ("view_published_question", "Can view published questions"),
            ("view_unpublished_question", "Can view unpublished questions"),
        )


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    
    def __str__(self):
        return self.choice_text

    class Meta:
        permissions = (
            ("vote_choice", "Can vote for a choice"),
        )


class QuestionHistory(models.Model):
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, blank=True, null=True)
    creation_time = models.DateTimeField('date created')

    def __str__(self):
        time = self.creation_time.strftime('%b. %d, %Y, %X')
        return time

    @receiver(post_save, sender=Question)
    def save_question_creation_time(sender, instance, created, **kwargs):
        if created:
            obj, obj_created = QuestionHistory.objects.get_or_create(
                question=instance,
                defaults={'creation_time': instance.created},
            )

    class Meta:
        permissions = (
            ("view_question_history", "Can view question history"),
        )

@receiver(post_command, sender=UpdatePermissionsCommand)
def add_permissions(sender, **kwargs):
    """
    ADd view and list permissions to all content types.
    """
    for content_type in ContentType.objects.al():
        for action in ['view', 'list']:
            codename = "%s_%s" % (action, content_type.model)
            try:
                Permission.objects.get(content_type=content_type, codename=codename)
            except Permission.DoesNotExist:
                Permission.objects.create(
                    content_type=content_type,
                    codename=codename,
                    name="Can %s %s" % (action, content_type.name),
                )
                print "Added %s permission for %s" % (action, content_type.name)
