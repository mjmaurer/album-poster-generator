from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^spotify_auth$', views.spotify_auth, name='spotify_auth'),
    url(r'^spotify_setup$', views.spotify_setup, name='spotify_setup'),
]