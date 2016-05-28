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


def spotify_setup(request):
    template = loader.get_template('poster/spotifysetup.html')
    return HttpResponse(template.render(request))

def spotify_auth(request):
    sp_oauth = oauth2.SpotifyOAuth(ids.SPOTIFY_CLIENT_ID, ids.SPOTIFY_APP_SECRET,
        "http://127.0.0.1:8000/spotify_auth", scope=sscopes.USER_TOP_READ)

    # TODO bad username handling

    if request.GET.get("code") is not None:
        # Spotify is returning with access code
        code = request.GET.get("code")
        try:
            token_info = sp_oauth.get_access_token(code)
        except:
            # TODO return error page
            template = loader.get_template('poster/index.html')
            return HttpResponse(template.render(request)) 
        return spotify_main(token_info['access_token'])
    else:
        # Must go to Spotify to get access code
        auth_url = sp_oauth.get_authorize_url()
        return HttpResponseRedirect(auth_url)

    
# Accepts a token
def spotify_main(request):
    token = request

    if type(token) is not unicode:
        # TODO return error page
        template = loader.get_template('poster/index.html')
        return HttpResponse(template.render(request)) 
    
    sp = spotipy.Spotify(auth=token)
    try:
        result = sp.current_user_top_artists(limit=50, offset=0, time_range='long_term')
        return HttpResponse(str(result))
    except:
        # TODO session has expired
        template = loader.get_template('poster/index.html')
        return HttpResponse(template.render(request)) 