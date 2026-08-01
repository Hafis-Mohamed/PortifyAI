from django.urls import path
from . import views

urlpatterns=[
    #home url
    path("",views.index,name="index"),

    #authentication urls
    path("user_registration/",views.userRegistration,name="userRegistration"),
    path("user_login/",views.userLogin,name="userLogin"),
    path("user_logout/",views.userLogout,name="userLogout"),

]