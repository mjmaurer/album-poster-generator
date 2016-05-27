from django.shortcuts import render
from django.template import loader

from django.http import HttpResponse


def index(request):
    template = loader.get_template('poster/index.html')
    return HttpResponse(template.render(request))


def spotify(request):
    return HttpResponse("Hello, world. You're at the polls index.")