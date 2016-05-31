from django.shortcuts import render
from django.template import loader

from spotipy import oauth2
import spotipy

from django.http import HttpResponse
from django.http import HttpRequest
from django.http import HttpResponseRedirect

import ids
import spotify_scopes as sscopes

def index(request):
    template = loader.get_template('poster/index.html')
    return HttpResponse(template.render(request))

def poster_dim_from_session(request):
    if request.session.get('poster_col') and request.session.get('poster_row'):
        return (request.session.get('poster_row'), request.session.get('poster_col'))
    else:
        raise Exception("No query args present for dimensions")

def spotify_setup(request):
    template = loader.get_template('poster/spotifysetup.html')
    return HttpResponse(template.render(request))

def spotify_auth(request):
    sp_oauth = oauth2.SpotifyOAuth(ids.SPOTIFY_CLIENT_ID, ids.SPOTIFY_APP_SECRET,
        "http://127.0.0.1:8000/spotify_auth", scope=sscopes.USER_TOP_READ)

    # TODO bad username handling

    # Store poster dimensions in session
    if request.GET.get("row") is not None and request.GET.get("col") is not None:
        request.session['poster_col'] = request.GET.get("col")
        request.session['poster_row'] = request.GET.get("row")

    if request.GET.get("code") is not None:
        # Spotify is returning with access code
        code = request.GET.get("code")
        try:
            token_info = sp_oauth.get_access_token(code)
        except:
            # TODO return error page
            template = loader.get_template('poster/index.html')
            return HttpResponse(template.render(request)) 
        return spotify_main(token_info['access_token'], request)
    else:
        # Must go to Spotify to get access code
        auth_url = sp_oauth.get_authorize_url()
        return HttpResponseRedirect(auth_url)

    
# Accepts a token
def spotify_main(token, request):

    sp = spotipy.Spotify(auth=token)
    try:
        row, col = poster_dim_from_session(request) 
        result = sp.current_user_top_artists(limit=50, offset=0, time_range='long_term')
        template = loader.get_template('poster/postersetup.html')
        return HttpResponse(template.render(request)) 
    except spotipy.SpotifyException as e:
        print("SESSION HAS EXPIRED ", e)
        # TODO session has expired
        template = loader.get_template('poster/index.html')
        return HttpResponse(template.render(request)) 
    except Exception as e:
        print('My exception occurred, value:', e)
        # TODO session has expired
        template = loader.get_template('poster/index.html')
        return HttpResponse(template.render(request)) 
