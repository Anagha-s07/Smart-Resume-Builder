from django.urls import path
from . import views
from .views import company_applicants
from .recommendations import job_recommendations

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/user/", views.register_user, name="register_user"),
    path("register/company/", views.register_company, name="register_company"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("my-resumes/", views.my_resumes, name="my_resumes"),
    path("my-profile/", views.my_profile, name="my_profile"),
    path("logout/", views.logout_view, name="logout"),
    path("company-applicants/", company_applicants, name="company_applicants"),

    # Dedicated ML-based job recommendation page
    path(
        "job-recommendations/",
        job_recommendations,
        name="job_recommendations",
    ),
]