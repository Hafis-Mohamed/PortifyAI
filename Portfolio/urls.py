from django.urls import path
from . import views

urlpatterns=[
    path("fetching_details/",views.fetchingDetails,name="fetchingDetails"),
    path("upload_resume/",views.uploadResume,name="uploadResume"),
    path("edit_details/",views.editDetails,name="editDetails"),
    path("generating_portfolio/",views.generatingPortfolio,name="generatingPortfolio"),
    path("process_portfolio/",views.processPortfolio,name="processPortfolio"),
    path("choose_template/",views.chooseTemplate,name="chooseTemplate"),
    path("preview/<str:template_id>/",views.previewPortfolio,name="previewPortfolio"),
    path("save_template/",views.saveTemplateChoice,name="saveTemplateChoice"),
    path("deployment_success/",views.deploymentSuccess,name="deploymentSuccess"),
    path("download_zip/<str:template_id>/",views.download_portfolio_zip,name="downloadPortfolioZip"),
]