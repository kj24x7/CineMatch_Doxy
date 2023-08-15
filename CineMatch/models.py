## Import statements
from django.db import models
from django.contrib.auth.models import User


## Models for questionnaire categories
class Questionnaire(models.Model):
    genre_select = models.CharField(max_length=100, choices=(
        ('', '----------------------'),
        ('HORROR', 'Horror'),
        ('ROMANCE', 'Romance'),
        ('COMEDY', 'Comedy'),
        ('ACTION', 'Action'),
        ('DOCUMENTARY', 'Documentary'),
    ))
    actor_select = models.CharField(max_length=200)
    director_select = models.CharField(max_length=200)
    rating_select = models.CharField(max_length=100, choices=(
        ('', '----------------------'),
        ('LOWEST', 'Lowest First'),
        ('HIGHEST', 'Highest First'),
        ('NO_PREFERENCE', 'No Preference'),
    ))

    def __str__(self):
        return f"Questionnaire {self.pk}"


class FavoriteMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie_id = models.IntegerField()  ## Storing the TMDB movie ID for each favorite movie
    movie_title = models.CharField(max_length=200)
    ## Add any other fields you want to store for favorite movies

    def __str__(self):
        return f"{self.user.username} - {self.movie_title}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.user.username
