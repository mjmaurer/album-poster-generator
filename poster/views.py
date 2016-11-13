from django.shortcuts import render
from django.template import loader, Context

from spotipy import oauth2
import spotipy

from django.http import HttpResponse
from django.http import HttpRequest
from django.http import HttpResponseRedirect
import sys, os

from sets import Set

from gmusicapi import Mobileclient
import musicbrainzngs
import ids
import spotify_scopes as sscopes

def index(request):
    template = loader.get_template('poster/index.html')
    return HttpResponse(template.render(request))

def poster_dim_from_session(request):
    if request.session.get('poster_col') and request.session.get('poster_row'):
        return (int(request.session.get('poster_row')), int(request.session.get('poster_col')))
    else:
        raise Exception("No query args present for dimensions")

def build_poster_template_context(rows, cols, artists, spotipy):
    context = {}
    context['artist_rows'] = {}
    context['span_sized'] = "span" + str(12 / cols)
    for i in range(rows):
        newRow = {}
        for j in range(cols):
            albums_result = spotipy.artist_albums(artists[i * cols + j][0], album_type='album', country="US", limit=15)
            if (len(albums_result['items']) == 0):
                albums_result = spotipy.artist_albums(artists[i * cols + j][0], limit=5)
            album_data = parse_albums(albums_result)
            newRow[j] = album_data
        context['artist_rows'][i] = newRow
    return context


def parse_albums(albums_result):
    result = {}

    seen = Set()

    for album in albums_result["items"]:
        if (len(album['images']) > 0 and album['images'][0]['url'] not in seen):
            result[album['name']] =  album['images'][0]['url'] if len(album['images']) > 0 else "{% static 'poster/img/default_album.png' %}"
            seen.add(album['images'][0]['url'])
        print album['name']
        print album['images'][0]['url']
        print len(album['images'])
        # TODO default pic for no 
    return result

def get_artist_ids(result):
    artists = []
    for artist in result['items']:
        print (artist['id'], artist['name'])
        artists.append((artist['id'], artist['name']))
    return artists

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
            request.session['code'] = sp_oauth.get_access_token(code)['access_token']
        except:
            # TODO return error page
            template = loader.get_template('poster/index.html')
            return HttpResponse(template.render(request)) 
        return spotify_setup(request)
    else:
        # Must go to Spotify to get access code
        auth_url = sp_oauth.get_authorize_url()
        return HttpResponseRedirect(auth_url)

    
# Accepts a token
def spotify_main(request):

    # Store poster dimensions in session
    if request.GET.get("row") is not None and request.GET.get("col") is not None:
        request.session['poster_col'] = request.GET.get("col")
        request.session['poster_row'] = request.GET.get("row")

    # musicbrainzngs.set_useragent("Album art poster generator", ".1", "mjmaurer777@gmail.com")
    # return HttpResponse(str(musicbrainzngs.get_release_group_image_list("8ea1c67a-4f1a-4eb0-887a-f249e782b6f8")))


    # api = Mobileclient()
    # api.login('mjmaurer777@gmail.com', '', Mobileclient.FROM_MAC_ADDRESS)
    # return HttpResponse(str(api.search("Brendan kelly and the wandering birds id rather die"))) 
  
    if ("code" in request.session):
        token = request.session["code"]
    else:
        return spotify_auth(request)

    sp = spotipy.Spotify(auth=token)
    try:
        row, col = poster_dim_from_session(request) 
        result = sp.current_user_top_artists(limit=row * col, offset=0, time_range='medium_term')
        artists = get_artist_ids(result)
        context = build_poster_template_context(row, col, artists, sp)
        template = loader.get_template('poster/postersetup.html')
        return HttpResponse(template.render(context, request)) 
    except spotipy.SpotifyException as e:
        print("SESSION HAS EXPIRED ", e)
        # TODO session has expired
        template = loader.get_template('poster/index.html')
        return HttpResponse(template.render(request)) 
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print('My exception occurred, value:', e)
        # TODO session has expired and take this sys shit out
        template = loader.get_template('poster/index.html')
        return HttpResponse(template.render(request)) 
