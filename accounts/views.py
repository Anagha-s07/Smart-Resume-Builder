
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .forms import UserRegistrationForm, CompanyRegistrationForm
from .models import UserProfile
from resume.models import Job, Resume, Application
from resume.ml_matching import calculate_resume_job_match


def home(request):
    return render(request, "accounts/login.html")


def register_user(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            full_name = form.cleaned_data["full_name"]
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name,
            )

            UserProfile.objects.create(
                user=user,
                role="user",
            )

            login(request, user)
            return redirect("dashboard")
    else:
        form = UserRegistrationForm()

    return render(
        request,
        "accounts/register_user.html",
        {"form": form},
    )


def register_company(request):
    if request.method == "POST":
        form = CompanyRegistrationForm(request.POST)

        if form.is_valid():
            company_name = form.cleaned_data["company_name"]
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            company_description = form.cleaned_data[
                "company_description"
            ]

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

            UserProfile.objects.create(
                user=user,
                role="company",
                company_name=company_name,
                company_description=company_description,
            )

            login(request, user)
            return redirect("dashboard")
    else:
        form = CompanyRegistrationForm()

    return render(
        request,
        "accounts/register_company.html",
        {"form": form},
    )


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        return render(
            request,
            "accounts/login.html",
            {"error": "Invalid username or password."},
        )

    return render(request, "accounts/login.html")


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.user.is_superuser:
        return redirect("/admin/")

    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("login")

    # Company dashboard: retain existing company functionality.
    if profile.role == "company":
        jobs = Job.objects.filter(
            company=request.user
        ).order_by("-posted_at")

        return render(
            request,
            "accounts/company_dashboard.html",
            {
                "profile": profile,
                "jobs": jobs,
                "total_jobs": jobs.count(),
                "active_jobs": jobs.filter(is_active=True).count(),
            },
        )

    # Normal user dashboard.
    resumes = Resume.objects.filter(
        user=request.user
    ).order_by("-created_at")

    resume = resumes.first()

    jobs = Job.objects.filter(
        is_active=True
    ).select_related("company").order_by("-posted_at")

    applications_count = Application.objects.filter(
        applicant=request.user
    ).count()

    recommended_jobs = []

    if resume:
        for job in jobs:
            match_percentage = calculate_resume_job_match(
                resume,
                job,
            )

            recommended_jobs.append({
                "job": job,
                "match_percentage": match_percentage,
            })

        recommended_jobs.sort(
            key=lambda item: item["match_percentage"],
            reverse=True,
        )

    return render(
        request,
        "accounts/user_dashboard.html",
        {
            "profile": profile,
            "recommended_jobs": recommended_jobs[:3],
            "resumes_count": resumes.count(),
            "jobs_count": jobs.count(),
            "applications_count": applications_count,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def my_resumes(request):
    resumes = Resume.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "accounts/my_resumes.html",
        {"resumes": resumes},
    )


@login_required
def my_profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("login")

    return render(
        request,
        "accounts/my_profile.html",
        {"profile": profile},
    )


@login_required
def company_applicants(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("dashboard")

    if profile.role != "company":
        return redirect("dashboard")

    applications = Application.objects.filter(
        job__company=request.user
    ).select_related(
        "job",
        "applicant",
    ).order_by("-applied_at")

    return render(
        request,
        "accounts/company_applicants.html",
        {
            "profile": profile,
            "applications": applications,
        },
    )
