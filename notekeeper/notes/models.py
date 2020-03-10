from django.db import models
from django import forms
from django.shortcuts import redirect
from django.utils.text import slugify
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.core.signing import Signer
from django.utils.html import mark_safe
import markdown
import uuid
from django.urls import reverse
from unidecode import unidecode
import markdown.extensions.fenced_code
import markdown.extensions.codehilite
import markdown.extensions.tables
import markdown.extensions.toc
from django_cryptography.fields import encrypt


def generate_unique_slug(_class, field):
    """
        return unique slug if origin slug is exist.
        eg: `foo-bar` => `foo-bar-1`
        :param `field` is specific field for title.
    """
    origin_slug = slugify(field)
    unique_slug = origin_slug
    numb = 1
    while _class.objects.filter(slug=unique_slug).exists():
        unique_slug = '%s-%d' % (origin_slug, numb)
        numb += 1
    return unique_slug


class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note_title = models.CharField(max_length=200)
    note_content = encrypt(models.TextField(null=True, blank=True))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=200, unique=True)
    tags = TaggableManager()
    signer = Signer(salt='notes.Note')

    def get_message_as_markdown(self):
        return mark_safe(
            markdown.markdown(
                self.note_content,
                extensions=['codehilite', 'fenced_code', 'markdown_checklist.extension', 'tables', 'toc'],
                # extension_configs={
                #     'codehilite':{
                #         'linenums': True
                #     }
                # }
                output_format="html5"
            )
        )

    def get_signed_hash(self):
        signed_pk = self.signer.sign(self.pk)
        return signed_pk

    def get_absolute_url(self):
        return reverse('share_notes', args=(self.get_signed_hash(),))

    def __str__(self):
        return self.note_title

    def save(self, *args, **kwargs):
        title = unidecode(self.note_title)
        if self.slug:
            if slugify(title) != self.slug:
                self.slug = generate_unique_slug(Note, title)
        else:
            self.slug = generate_unique_slug(Note, title)
        super(Note, self).save(*args, **kwargs)


class AddNoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = '__all__'
        exclude = ['slug', 'user']
        widgets = {
            'tags': forms.TextInput(
                attrs={
                    'data-role':'tagsinput',
                }
            ),
        }
