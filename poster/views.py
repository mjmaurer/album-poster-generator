from django.shortcuts import render
from django.template import loader, Context
from wsgiref.util import FileWrapper

from spotipy import oauth2
import spotipy

import urllib
import cv2
import numpy as np
from PIL import Image

import pylast
import StringIO

from django.http import HttpResponse
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from lastfmhelper import LastFmHelper
import sys, os

import sys
from sets import Set

from util import get_period_from_string
from gmusicapi import Mobileclient
import musicbrainzngs
import ids
import spotify_scopes as sscopes

BASE_URL = "http://127.0.0.1:8000"

def index(request):
    template = loader.get_template('poster/index.html')
    return HttpResponse(template.render(request))

def poster_dim_from_session(request):
    if request.session.get('poster_col') and request.session.get('poster_row'):
        return (int(request.session.get('poster_row')), int(request.session.get('poster_col')))
    else:
        raise Exception("No query args present for dimensions")

def type_from_session(request):
    if request.session.get('type'):
        return request.session.get('type')
    else:
        raise Exception("No query args present for type")

def period_from_session(request):
    if request.session.get('timeperiod'):
        return request.session.get('timeperiod')
    else:
        raise Exception("No query args present for type")

# Context is:
# artist_rows : 
#   1 : [{title: url}, {title: url}, ...]
#   2 : ...
# span_sized:
#   12 / cols
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
        # print album['name']
        # print album['images'][0]['url']
        # print len(album['images'])
        # TODO default pic for no 
    return result

def get_artist_ids(result):
    artists = []
    for artist in result['items']:
        # print (artist['id'], artist['name'])
        artists.append((artist['id'], artist['name']))
    return artists

def spotify_setup(request):
    template = loader.get_template('poster/spotifysetup.html')
    return HttpResponse(template.render({"action" : "spotify_main"}, request))

def lastfm_setup(request):
    template = loader.get_template('poster/lastfmsetup.html')
    return HttpResponse(template.render({"action" : "lastfm_main"}, request))

def spotify_auth(request):
    sp_oauth = oauth2.SpotifyOAuth(ids.SPOTIFY_CLIENT_ID, ids.SPOTIFY_APP_SECRET,
        BASE_URL + "/spotify_auth", scope=sscopes.USER_TOP_READ)

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

def lastfm_auth(request):
    # TODO bad username handling
    network = pylast.LastFMNetwork(api_key = ids.LASTFM_KEY, api_secret =
        ids.LASTFM_APP_SECRET)

    if request.GET.get("token") is not None:
        # Spotify is returning with access code
        try:
            token = request.GET.get("token")
            sg = pylast.SessionKeyGenerator(network)
            my_session_key = sg.get_web_auth_session_key(BASE_URL, token)
            request.session['key'] = my_session_key
        except:
            print(sys.exc_info())
            # TODO return error page
            template = loader.get_template('poster/index.html')
            return HttpResponse(template.render(request))
        return lastfm_setup(request)
    else:
        # Must go to LastFM to get access code
        auth_url = "http://www.last.fm/api/auth/?api_key=" + ids.LASTFM_KEY + "&cb=" + BASE_URL + "/lastfm_auth"
        # auth_url = sg.get_web_auth_url()
        return HttpResponseRedirect(auth_url)

    
# Accepts a token
def spotify_main(request):
    # Store poster dimensions in session
    if request.GET.get("row") is not None and request.GET.get("col") is not None:
        request.session['poster_col'] = request.GET.get("col")
        request.session['poster_row'] = request.GET.get("row")

    if (request.GET.get("timeperiod") is not None):
        request.session['timeperiod'] = request.GET.get("timeperiod")
    else:
        request.session['timeperiod'] = "medium_term"


    if ("code" in request.session):
        token = request.session["code"]
    else:
        return spotify_auth(request)

    sp = spotipy.Spotify(auth=token)
    try:
        row, col = poster_dim_from_session(request) 
        result = sp.current_user_top_artists(limit=row * col, offset=0, time_range=period_from_session(request))
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

# Accepts a token
def lastfm_main(request):

    # Store poster dimensions in session
    if request.GET.get("row") is not None and request.GET.get("col") is not None:
        request.session['poster_col'] = request.GET.get("col")
        request.session['poster_row'] = request.GET.get("row")

    if (request.GET.get("timeperiod") is not None):
        request.session['timeperiod'] = get_period_from_string(request.GET.get("timeperiod"))
    else:
        request.session['timeperiod'] = pylast.PERIOD_OVERALL

    if (request.GET.get("type") is not None):
        request.session['type'] = request.GET.get("type")
    else:
        request.session['type'] = "Album"


    if ("key" in request.session):
        my_session_key = request.session["key"]
    else:
        return lastfm_auth(request)

    network = pylast.LastFMNetwork(api_key = ids.LASTFM_KEY, api_secret =
            ids.LASTFM_APP_SECRET, session_key = my_session_key)

    try:
        row, col = poster_dim_from_session(request)
        myType = type_from_session(request)
        period = period_from_session(request)
        user = network.get_authenticated_user()
        context = LastFmHelper.factory(myType, user, col, row, period).create_context()
        template = loader.get_template('poster/postersetup.html')
        return HttpResponse(template.render(context, request)) 
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print('My exception occurred, value:', e)
        # TODO session has expired and take this sys shit out
        template = loader.get_template('poster/index.html')
        return HttpResponse(template.render(request)) 

def pic_stitch(request):
    print request.POST
    urlList = request.POST.getlist('picUrls[]')
    albumNames = request.POST.getlist('albumNames[]')
    print albumNames
    urlList = urlList[0].split(",")
    albumNames = albumNames[0].split(",")
    img = make_tiled_image(urlList, albumNames, request)
    img = cv2.resize(img, (9600, 9600))
    print img.shape
    img = cv2.imencode('.jpg', img)[1].tostring()
    response = HttpResponse(FileWrapper(StringIO.StringIO(img)), content_type='image/jpeg')
    response['Content-Disposition'] = 'attachment; filename="pic.jpg"'
    return response

def url_to_image(url, albumName):
    # download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    print albumName + " " + url
    resp = urllib.urlopen(url)
    imageNp = np.asarray(bytearray(resp.read()), dtype="uint8")
    
    image = cv2.imdecode(imageNp, cv2.IMREAD_COLOR)
    if image == None:
        # buf = StringIO.StringIO()
        # Image.fromarray(imageNp).save(buf, "jpeg")
        # imageNp = np.asarray(bytearray(buf.read()), dtype="uint8")
        # image = cv2.imdecode(imageNp, cv2.IMREAD_COLOR)
        spotify = spotipy.Spotify()
        results = spotify.search(q='album:' + albumName, type='album')
        url = parse_albums(results['albums'])[albumName]
        resp = urllib.urlopen(url)
        imageNp = np.asarray(bytearray(resp.read()), dtype="uint8")
        print "retry"
        print imageNp.shape
        
        image = cv2.imdecode(imageNp, cv2.IMREAD_COLOR)
    else:
        print ""
    print type(image)
    print image.shape
    # return the image
    return image

def make_tiled_image(urlList, albumNames, request):
    print urlList
    print albumNames
    cvImages = map(lambda i: url_to_image(urlList[i], albumNames[i]), range(len(urlList)))
    row, col = poster_dim_from_session(request)
    w, h = (0, 0)
    for img in cvImages:
        w = max(w, img.shape[0])
        h = max(h, img.shape[1])

    w, h = max(w, h), max(w, h)
    for i in range(len(cvImages)):
        img = cvImages[i]
        if not img.shape[:2] == (w, h):
            print "resize"
            cvImages[i] = cv2.resize(img, (w, h))

    imageRows = ()
    for i in range(row):
        cvImagesInRow = cvImages[i*col:i*col+col]
        imageRows = imageRows + (np.concatenate(tuple(cvImagesInRow), axis=1),)

    return np.concatenate(imageRows, axis=0)

def get_album_pic_url_from_spotify(searchTerm):
    return