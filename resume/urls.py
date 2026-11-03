
from django.urls import path
from . import views

urlpatterns = [
    # Resume features
    path("create/", views.create_resume, name="create_resume"),

    path(
        "preview/<int:resume_id>/<str:template>/",
        views.resume_preview,
        name="resume_preview",
    ),

    path(
        "templates/<int:resume_id>/",
        views.template_selection,
        name="template_selection",
    ),

    path(
        "download/<int:resume_id>/<str:template>/",
        views.download_resume_pdf,
        name="download_resume_pdf",
    ),

    path(
        "edit/<int:resume_id>/",
        views.edit_resume,
        name="edit_resume",
    ),

    # Job features
    path("post-job/", views.post_job, name="post_job"),

    path("job/<int:job_id>/", views.job_detail, name="job_detail"),

    path(
        "job/<int:job_id>/apply/",
        views.apply_job,
        name="apply_job",
    ),

    
path("manage-jobs/", views.manage_jobs, name="manage_jobs"),
path(
    "manage-jobs/<int:job_id>/toggle/",
    views.toggle_job_status,
    name="toggle_job_status",
),
path(
    "manage-jobs/<int:job_id>/delete/",
    views.delete_job,
    name="delete_job",
),
]
