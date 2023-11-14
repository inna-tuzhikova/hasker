from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return HttpResponse('1Hello, world. You\'re at the polls index.')


def index_1(request):
    return HttpResponse('2Hello, world. You\'re at the polls index.')
