## Imports
import requests as req

from .config import config
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from mysite import settings
from .forms import QuestionnaireForm, BioForm
from .tokens import generate_token
from .models import FavoriteMovie, UserProfile
global movie_num

## initialize url for movie database
TMDB_BASE_URL = 'https://api.themoviedb.org/3/'
movie_num = 100


def home(request):
    """! Maps index html to home url
    @param request  send information to server.
    @return render HttpResponse object.
    """
    return render(request, "CineMatch/index.html")


def signin(request):
    """! sign in information requested, maps sign in html to sign in url
    @param request  send information to server.
    @return render HttpResponse object.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        pass1 = request.POST.get("pass1")

        user = authenticate(username=username, password=pass1)

        if user is not None:
            login(request, user)
            fname = user.first_name
            return render(request, "CineMatch/index.html", {"fname": fname})

        else:
            messages.error(request, "Invalid Login")
            return redirect("home")

    return render(request, "CineMatch/signin.html")


def signup(request):
    """! sign up information requested, maps sign up html to sign up url
     @param request  send information to server.
     @return render HttpResponse object.
     """
    if request.method == "POST":
        username = request.POST.get("username")
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        email = request.POST.get("email")
        pass1 = request.POST.get("pass1")
        pass2 = request.POST.get("pass2")

        if User.objects.filter(username=username):
            messages.error(request, "Username already exists.")
            return redirect("home")

        if User.objects.filter(email=email):
            messages.error(request, "Email already registered.")
            return redirect("home")

        if len(username) > 10:
            messages.error(request, "Username must be less than 10 characters.")

        if pass1 != pass2:
            messages.error(request, "Passwords do not match.")

        if not username.isalnum():
            messages.error(request, "Username must be alpha-numeric.")
            return redirect("home")

        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()

        messages.success(request, "Your account has been successfully created!")

        ## Welcome Email
        subject = "Welcome to CineMatch!"
        message = "Hello " + myuser.first_name + "! \n" + "Welcome to CineMatch! \n Thank you for registering. " \
                                                          "\n Please confirm your email address to continue. " \
                                                          "\n\n Best Regards, " \
                                                          "\n CineMatch Team"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        ## Email Address Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your CineMatch Email Address"
        message2 = render_to_string('email_confirmation.html', {
            "name": myuser.first_name,
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(myuser.pk)),
            "token": generate_token.make_token(myuser)
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()

        return redirect("home")

    return render(request, "CineMatch/signup.html")


def signout(request):
    """! sign out requested, maps sign out html to home
     @param request  send information to server.
     @return redirect to home.
     @return render HttpResponse object.
     """
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("home")


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect("home")

    else:
        return render(request, "activation_failed.html")


@login_required
def profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    favorite_movies = FavoriteMovie.objects.filter(user=user)

    if request.method == 'POST':
        bio_form = BioForm(request.POST, instance=user_profile)
        if bio_form.is_valid():
            bio_form.save()
            messages.success(request, "Bio saved successfully.")
    else:
        bio_form = BioForm(instance=user_profile)

    return render(request, "CineMatch/profile.html",
                  {"user": user, "favorite_movies": favorite_movies, "bio_form": bio_form})


def search(request):
    """! Questionnaire query initialized, maps search html to search url
    @param request  send information to server.
    @return render HttpResponse object.
    """
    form = QuestionnaireForm()

    if request.method == "POST":
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            actor = form.cleaned_data.get('actor_select').strip()
            director = form.cleaned_data.get('director_select').strip()
            genre = form.cleaned_data.get('genre_select')
            rating_preference = form.cleaned_data.get('rating_select', 'NO_PREFERENCE')

            print(f"Input genre_name: {genre}")
            genre_id = fetch_genre_id(genre)
            print(f"Matching genre: {genre_id}")

            ## Construct the query based on the user's search criteria
            if actor and genre and genre != 'NO_PREFERENCE':
                return redirect('recommendations', actor=actor, director='', genre=genre)
            elif actor and director:
                return redirect('recommendations', actor=actor, director=director, genre='')
            elif actor:
                return redirect('recommendations', actor=actor, director='', genre='')
            elif director:
                return redirect('recommendations', actor='', director=director, genre='')
            elif genre and genre != 'NO_PREFERENCE':
                return redirect('recommendations', actor='', director='', genre=genre)
            else:
                ## Handle the case where no criteria is selected
                error_message = "Please select an actor, director, or genre."
                return render(request, "CineMatch/search.html", {"form": form, "error_message": error_message})

    return render(request, "CineMatch/search.html", {"form": form})


def continue_to_search(request):
    return render(request, "CineMatch/search.html")


@login_required
def get_movie_recommendations(request, actor, director, genre):
    """! function to query database for filters.
    @param request  send information to server.
    @return movie data fetched.
    """
    global movie_num
    ## Get the query parameters from the URL
    actor_name = request.GET.get('actor_select', actor)
    director_name = request.GET.get('director_select', director)
    genre_name = request.GET.get('genre_select', genre)
    rating_preference = request.GET.get('rating_select', 'NO_PREFERENCE')

    ## Fetch movie data from TMDB API based on the query parameters
    if actor_name:
        print(f'Actor Selected')
        if genre_name and genre_name != 'NO_PREFERENCE':
            print(f'Actor and Genre Selected')
            movies = fetch_actor_genre_movies(actor_name, genre_name)
        elif director_name:
            print(f'Director and Actor selected')
            movies = fetch_movies_for_actor_in_director(actor_name, director_name)
        else:
            movies = fetch_actor_movies(actor_name)
    elif director_name:
        print(f'Director Selected')
        movies = fetch_director_movies(director_name)
    elif genre_name and genre_name != 'NO_PREFERENCE':
        print(f'Genre Selected')
        ## Convert genre ID to string before passing it to fetch_movie_data
        movies = fetch_movie_data(genre_name)
    else:
        ## Handle the case where no criteria is selected
        error_message = "Please select an actor, director, or genre."
        return render(request, "CineMatch/search.html", {"error_message": error_message})

    ## Sort movies based on rating preference (if applicable)
    if rating_preference == 'LOWEST':
        movies.sort(key=lambda x: x.get('vote_average', 0))
    elif rating_preference == 'HIGHEST':
        movies.sort(key=lambda x: x.get('vote_average', 0), reverse=True)

    ## Get the top 5 movie results
    top_movies = movies[:movie_num]
    print(f'returning movies from recommendations')
    user = request.user
    for movie in top_movies:
        movie_id = movie['id']
        movie_title = movie['title']
        movie['is_favorite'] = FavoriteMovie.objects.filter(user=user, movie_id=movie_id).exists()

    return render(request, "CineMatch/recommendations.html", {"movies": top_movies})


@login_required
def add_to_favorite(request, movie_id, movie_title):
    ## Check if the movie is already in the favorite list for the current user
    user = request.user

    ## Check the number of movies in the user's favorites list
    num_favorite_movies = FavoriteMovie.objects.filter(user=user).count()

    ## Limit the number of favorite movies to 15
    if num_favorite_movies >= 15:
        messages.warning(request, "You can only have up to 15 favorite movies.")
    else:
        ## Check if the movie is already in the favorite list for the current user
        if not FavoriteMovie.objects.filter(user=user, movie_id=movie_id).exists():
            ## Add the movie to the user's favorite list
            favorite_movie = FavoriteMovie(user=user, movie_id=movie_id, movie_title=movie_title)
            favorite_movie.save()
        else:
            ## Remove the movie from the user's favorite list
            FavoriteMovie.objects.filter(user=user, movie_id=movie_id).delete()

    return redirect('profile')


def fetch_movie_data(genre_id, actor_id=None, director_id=None):
    """! function to query database for movie data ids
    @param request  send information to server.
    @return movie data fetched.
    """
    print(f'Genre ID: {genre_id}, Actor ID: {actor_id}, Director ID: {director_id}')

    api_url = f'https://api.themoviedb.org/3/discover/movie'
    params = {
        'api_key': config.api_key,
        'with_genres': genre_id,
        'sort_by': 'popularity.desc',
        'include_adult': 'false',
        'include_video': 'false'
    }

    ## Add the actor ID to the request parameters if it's provided
    if actor_id:
        params['with_cast'] = actor_id

    ## Add the director's ID to the request parameters if it's provided
    if director_id:
        params['with_crew'] = director_id

    try:
        response = req.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        movies = data.get('results', [])
        return movies
    except req.exceptions.RequestException as e:
        ## Handle API request errors here
        print(f"Error fetching movie data: {e}")
        return []


def fetch_genre_id(genre_name):
    """! function to query database for genre id.
    @param request  send information to server.
    @return movie data fetched.
    """
    api_url = f'https://api.themoviedb.org/3/genre/movie/list'
    params = {
        'api_key': config.api_key,
        'language': 'en-US'
    }

    try:
        response = req.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        genres = data.get('genres', [])

        print(f"Input genre_name: {genre_name}")
        print("Available genres:")
        for genre in genres:
            print(f"{genre.get('name')} - {genre.get('id')}")

        for genre in genres:
            if genre_name.lower() == genre.get('name', '').lower():
                return str(genre.get('id'))
        return None
    except req.exceptions.RequestException as e:
        ## Handle API request errors here
        print(f"Error fetching genre ID: {e}")
        return None


def fetch_actor_id(actor_name):
    """! function to query database for actor id searched.
    @param request  send information to server.
    @return movie data fetched.
    """
    api_url = f'https://api.themoviedb.org/3/search/person'
    params = {
        'api_key': config.api_key,
        'query': actor_name,
    }

    try:
        response = req.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        actor_results = data.get('results', [])

        if not actor_results:
            print(f"No actors found for the given name: {actor_name}")
            return None

        ## Get the ID of the first actor in the search results
        actor_id = actor_results[0].get('id')
        return actor_id
    except req.exceptions.RequestException as e:
        ## Handle API request errors here
        print(f"Error fetching actor ID: {e}")
        return None


def fetch_director_id(director_name):
    """! function to query database for directors id searched.
    @param request  send information to server.
    @return movie data fetched.
    """
    api_url = f'https://api.themoviedb.org/3/search/person'
    params = {
        'api_key': config.api_key,
        'query': director_name,
    }

    try:
        response = req.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        director_results = data.get('results', [])
        ## Iterate through the results to find the best match for the director name
        for result in director_results:
            if director_name.lower() in result.get('name', '').lower():
                return result.get('id')
        return None
    except req.exceptions.RequestException as e:
        ## Handle API request errors here
        print(f"Error fetching director ID: {e}")
        return None


def fetch_actor_movies(actor_name):
    """! function to query database for actors searched.
    @param request  send information to server.
    @return movie data fetched.
    """
    base_url = 'https://api.themoviedb.org/3'
    endpoint = '/search/person'

    ## Search for actors based on the given name
    params = {
        'api_key': config.api_key,
        'language': 'en-US',
        'query': actor_name
    }

    try:
        response = req.get(base_url + endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        actors = data.get('results', [])

        ## Iterate through the actors to find an exact match for the given name
        for actor in actors:
            if actor_name.lower() == actor.get('name', '').lower():
                actor_id = actor.get('id')
                ## Fetch movies starring the actor based on their ID
                endpoint = f'/person/{actor_id}/movie_credits'
                params = {
                    'api_key': config.api_key,
                    'language': 'en-US',
                }
                response = req.get(base_url + endpoint, params=params)
                response.raise_for_status()
                data = response.json()
                movies = data.get('cast', [])
                print(f'fetch_actor_movies')
                return movies

        ## Handle the case where the actor name is not found
        print(f"No actors found for the given name: {actor_name}")
        return []

    except req.exceptions.RequestException as e:
        ## Handle API request errors
        print(f"Error fetching actor movies: {e}")
        return []


def fetch_actor_genre_movies(actor_name, genre_name):
    """! function to query database for actors and genres commonalities.
    @param request  send information to server.
    @return movie data fetched.
    """
    ## First, fetch the actor's ID
    actor_id = fetch_actor_id(actor_name)

    if not actor_id:
        ## Handle the case where the actor is not found
        print(f'No actor_id')
        return []

    if not genre_name:
        ## Handle the case where the genre is not found
        print(f'No genre_id')
        return []

    ## Finally, fetch movies based on both the actor ID and genre ID
    return fetch_movie_data(genre_name, actor_id)


def fetch_director_movies(director_name):
    """! function to query database for directors searched.
    @param request  send information to server.
    @return movie data fetched.
    """
    base_url = 'https://api.themoviedb.org/3'
    endpoint = '/search/person'

    ## Search for the director's ID based on their name
    params = {
        'api_key': config.api_key,
        'language': 'en-US',
        'query': director_name
    }

    try:
        response = req.get(base_url + endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        directors = data.get('results', [])
        if not directors:
            print(f"No directors found for the given name: {director_name}")
            return []

        ## Get the ID of the first director in the search results
        director_id = directors[0]['id']

        ## Fetch all movies that have the director's ID in the crew
        endpoint = f'/discover/movie'
        params = {
            'api_key': config.api_key,
            'language': 'en-US',
            'with_crew': f'{director_id}',
            'sort_by': 'popularity.desc',
            'include_adult': 'false',
            'include_video': 'false'
        }

        response = req.get(base_url + endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        all_movies = data.get('results', [])

        director_movies = []

        ## Fetch credits data for each movie and filter the movies based on director's name
        for movie in all_movies:
            movie_id = movie['id']
            credits_endpoint = f'/movie/{movie_id}/credits'
            credits_params = {
                'api_key': config.api_key,
                'language': 'en-US'
            }

            credits_response = req.get(base_url + credits_endpoint, params=credits_params)
            credits_response.raise_for_status()
            credits_data = credits_response.json()
            crew = credits_data.get('crew', [])

            ## Check if the director's name is in the crew and has a job of 'Director'
            if any(credit['name'] == director_name and credit['job'] == 'Director' for credit in crew):
                director_movies.append(movie)

        return director_movies

    except req.exceptions.RequestException as e:
        ## Handle API request errors here
        print(f"Error fetching movie data: {e}")
        return []


def fetch_movies_for_actor_in_director(actor_name, director_name):
    """! function to query database for actors and directors commonalities.
    @param request  send information to server.
    @return movie data fetched.
    """
    base_url = 'https://api.themoviedb.org/3'

    ## Fetch the actor's ID
    actor_id = fetch_actor_id(actor_name)

    if not actor_id:
        print(f'No actor_id found for: {actor_name}')
        return []

    ## Fetch the director's ID
    director_id = fetch_director_id(director_name)

    if not director_id:
        print(f'No director_id found for: {director_name}')
        return []

    print(f'Actor ID: {actor_id}, Director ID: {director_id}')

    ## Fetch movies based on the actor ID and director ID
    actor_movies = fetch_movie_data(genre_id=None, actor_id=actor_id, director_id=None)
    director_movies = []

    ## Fetch credits data for each movie and filter the movies based on director's name
    for movie in actor_movies:
        movie_id = movie['id']
        credits_endpoint = f'/movie/{movie_id}/credits'
        credits_params = {
            'api_key': config.api_key,
            'language': 'en-US'
        }

        credits_response = req.get(base_url + credits_endpoint, params=credits_params)
        credits_response.raise_for_status()
        credits_data = credits_response.json()
        crew = credits_data.get('crew', [])

        ## Check if the director's name is in the crew and has a job of 'Director'
        if any(credit['name'] == director_name and credit['job'] == 'Director' for credit in crew):
            director_movies.append(movie)

    ## Find movies where both actor and director have worked together
    common_movies = [movie for movie in actor_movies if movie in director_movies]

    return common_movies
