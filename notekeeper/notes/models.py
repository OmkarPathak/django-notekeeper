from django.db import models
from django import forms
from django.shortcuts import redirect
from django.utils.text import slugify
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.core.signing import Signer
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget
import uuid


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
    note_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=200, unique=True)
    tags = TaggableManager()
    signer = Signer(salt='notes.Note')

    def get_signed_hash(self):
        print('pk:', self.pk)
        signed_pk = self.signer.sign(self.pk)
        return signed_pk

    def __str__(self):
        return self.note_title

    def save(self, *args, **kwargs):
        if self.slug:
            if slugify(self.note_title) != self.slug:
                self.slug = generate_unique_slug(Note, self.note_title)
        else:
            self.slug = generate_unique_slug(Note, self.note_title)
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
            'note_content': SummernoteInplaceWidget(),
        }
