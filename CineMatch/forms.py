## Import statements
from django import forms
from .models import Questionnaire, UserProfile

## Form for questionnaire created
class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ['genre_select', 'actor_select', 'director_select', 'rating_select']


class BioForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }