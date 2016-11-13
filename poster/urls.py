from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^spotify_auth$', views.spotify_auth, name='spotify_auth'),
    url(r'^spotify_setup$', views.spotify_setup, name='spotify_setup'),
    url(r'^spotify_main$', views.spotify_main, name='spotify_main'),
    url(r'^lastfm_setup$', views.spotify_setup, name='lastfm_setup'),
]