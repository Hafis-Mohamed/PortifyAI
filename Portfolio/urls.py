from django.urls import path
from . import views

urlpatterns=[
    path("fetching_details/",views.fetchingDetails,name="fetchingDetails"),
    path("upload_resume/",views.uploadResume,name="uploadResume"),
    path("edit_details/",views.editDetails,name="editDetails"),
]