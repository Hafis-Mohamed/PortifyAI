from django.urls import path
from . import views

urlpatterns=[
    path("",views.index,name="index"),
    path("user_registration/",views.userRegistration,name="userRegistration"),
]