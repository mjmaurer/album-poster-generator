from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^spotify_auth$', views.spotify_auth, name='spotify_auth'),
    url(r'^spotify_setup$', views.spotify_setup, name='spotify_setup'),
    url(r'^spotify_main$', views.spotify_main, name='spotify_main'),
    url(r'^lastfm_setup$', views.lastfm_setup, name='lastfm_setup'),
    url(r'^lastfm_auth$', views.lastfm_auth, name='lastfm_auth'),
    url(r'^lastfm_main$', views.lastfm_main, name='lastfm_main'),
]