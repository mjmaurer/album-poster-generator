from django.shortcuts import render
from django.template import loader, Context
from wsgiref.util import FileWrapper
from random import randint

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
from spotifyhelper import SpotifyHelper
import sys, os

import sys
from sets import Set

import util
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

def spotify_setup(request):
    template = loader.get_template('poster/spotifysetup.html')
    return HttpResponse(template.render({"action" : "spotify_main"}, request))

def lastfm_setup(request):
    template = loader.get_template('poster/lastfmsetup.html')
    return HttpResponse(template.render({"action" : "lastfm_main"}, request))

def custom_setup(request):
    template = loader.get_template('poster/freeformsetup.html')
    return HttpResponse(template.render({"action" : "custom_main"}, request))

def custom_main(request):
    if request.GET.get("row") is not None and request.GET.get("col") is not None:
        request.session['poster_col'] = request.GET.get("col")
        request.session['poster_row'] = request.GET.get("row")

    template = loader.get_template('poster/freeformmain.html')
    return HttpResponse(template.render(
        util.build_custom_template_context(int(request.session['poster_row']), int(request.session['poster_col'])), request))

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

    if (request.GET.get("type") is not None):
        request.session['type'] = request.GET.get("type")
    else:
        request.session['type'] = "Artist"

    sp = spotipy.Spotify(auth=token)
    try:
        row, col = poster_dim_from_session(request) 
        myType = type_from_session(request)
        period = period_from_session(request)
        context = SpotifyHelper.factory(myType, sp, col, row, period).create_context()
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
        request.session['type'] = "Artist"


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


def wait_for_load(request):
    if "url_list" not in request.session:
        # TODO display error page
        template = loader.get_template('poster/index.html')
        return HttpResponse(template.render(request))

    urlList = request.session["url_list"]
    albumNames = request.session["album_names"]
    myType = type_from_session(request)

    print "Ablum name"
    print albumNames
    if myType == 'Album':
        img = make_tiled_image(urlList, albumNames, request)
    else:
        img = make_tiled_image_artist(urlList, albumNames, request)
    scale = 9000.0 / img.shape[0] 
    # TODO Try to compress or something
    img = cv2.resize(img, (int(img.shape[0] * scale), int(scale * img.shape[1])))
    print img.shape
    img = cv2.imencode('.jpg', img)[1].tostring()
    response = HttpResponse(FileWrapper(StringIO.StringIO(img)), content_type='image/jpeg')
    response['Content-Disposition'] = 'attachment; filename="pic.jpg"'
    return response


def pic_stitch(request):
    print request.POST
    urlList = request.POST.getlist('picUrls')

    albumNames = None
    if request.POST.getlist('albumNames') is not None:
        albumNames = request.POST.getlist('albumNames')
        albumNames = albumNames[0].split(",")
    
    request.session['album_names'] = albumNames
    urlList = urlList[0].split(",")
    request.session['url_list'] = urlList
    

    template = loader.get_template('poster/loading.html')
    return HttpResponse(template.render(request))     
    

def url_to_image(url, name, myType):
    # download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    resp = urllib.urlopen(url)
    imageNp = np.asarray(bytearray(resp.read()), dtype="uint8")
    try:
        image = cv2.imdecode(imageNp, cv2.IMREAD_COLOR)
    except:
        image = None
        print "Error occured: " + str(sys.exc_info()[0])
    if image == None:
        # buf = StringIO.StringIO()
        # Image.fromarray(imageNp).save(buf, "jpeg")
        # imageNp = np.asarray(bytearray(buf.read()), dtype="uint8")
        # image = cv2.imdecode(imageNp, cv2.IMREAD_COLOR)
        spotify = spotipy.Spotify()
        if myType == 'Artist':
            results = spotify.search(q='artist:' + name, type='artist')
            result = results['artists']
        else:
            results = spotify.search(q='album:' + name, type='album')
            result = results['albums']
        url = util.parse_albums(result).values()[0]
        resp = urllib.urlopen(url)
        imageNp = np.asarray(bytearray(resp.read()), dtype="uint8")
        # TODO if spotify couldn't find anything
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
    cvImages = map(lambda i: url_to_image(urlList[i], albumNames[i], 'Album'), range(len(urlList)))
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

def make_tiled_image_artist(urlList, artistNames, request):
    print urlList
    print len(artistNames)
    if (artistNames is not None and len(artistNames) > 1):
        cvImages = map(lambda i: url_to_image(urlList[i], artistNames[i], "Artist"), range(len(urlList)))
    else:
        cvImages = map(lambda i: url_to_image(urlList[i], "", "Artist"), range(len(urlList)))
    print len(cvImages)
    row, col = poster_dim_from_session(request)

    w = 0
    for img in cvImages:
        w = max(w, img.shape[1])

    # Go column by column, resize first
    for colIndex in range(col):
        for i in range(len(cvImages))[colIndex:row * col + 1:row]:
            img = cvImages[i]
            if (not img.shape[1] == w):
                size_ratio = img.shape[0] / float(img.shape[1])
                print size_ratio
                cvImages[i] = cv2.resize(img, (w, int(w * size_ratio)))
                print cvImages[i].shape
        print "New column"

    # Create each column
    h = 0
    imageCols = ()
    for colIndex in range(col):
        cvImagesInCol = cvImages[colIndex:row * col + 1:row]
        column = np.concatenate(tuple(cvImagesInCol), axis=0)
        h = max(h, column.shape[0])
        imageCols = imageCols + (column,)
        print column.shape

    print (h,w * col,3)
    blank_image = np.zeros((h,w * col,3), np.uint8)
    for i in range(col):
        column = imageCols[i]
        widthStart = w * i
        heightStart = randint(0, h - column.shape[0])
        blank_image[heightStart:heightStart+column.shape[0], widthStart:widthStart+w] = column

    return blank_image