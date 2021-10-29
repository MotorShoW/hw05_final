from django.contrib.auth import get_user_model
from django.forms import ModelForm

from .models import Comment, Post

User = get_user_model()


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'group': 'Группа',
            'text': 'Текст',
            'image': 'Картинка',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
