
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from resume.models import Job, Resume
from resume.ml_matching import calculate_resume_job_match
from .models import UserProfile


@login_required
def job_recommendations(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None

    # Companies should use their company dashboard, not job recommendations.
    if profile and profile.role == "company":
        from django.shortcuts import redirect
        return redirect("dashboard")

    resume = Resume.objects.filter(
        user=request.user
    ).order_by("-created_at").first()

    jobs = Job.objects.filter(
        is_active=True
    ).select_related("company")

    search_query = request.GET.get("q", "").strip()
    selected_location = request.GET.get("location", "").strip()
    selected_type = request.GET.get("type", "").strip()
    selected_sort = request.GET.get("sort", "match").strip()

    if search_query:
        jobs = jobs.filter(
            Q(job_title__icontains=search_query)
            | Q(required_skills__icontains=search_query)
            | Q(job_description__icontains=search_query)
            | Q(qualification__icontains=search_query)
            | Q(location__icontains=search_query)
        )

    if selected_location:
        jobs = jobs.filter(
            location__icontains=selected_location
        )

    if selected_type:
        jobs = jobs.filter(
            employment_type__iexact=selected_type
        )

    recommended_jobs = []
    employment_types = sorted(
        Job.objects.filter(is_active=True)
        .exclude(employment_type="")
        .values_list("employment_type", flat=True)
        .distinct()
    )

    if resume:
        for job in jobs:
            match_percentage = calculate_resume_job_match(
                resume,
                job,
            )

            company_profile = UserProfile.objects.filter(
                user=job.company
            ).first()

            if company_profile and company_profile.company_name:
                company_name = company_profile.company_name
            else:
                company_name = (
                    job.company.get_full_name()
                    or job.company.username
                )

            recommended_jobs.append({
                "job": job,
                "match_percentage": match_percentage,
                "company_name": company_name,
            })

    else:
        for job in jobs:
            company_profile = UserProfile.objects.filter(
                user=job.company
            ).first()

            if company_profile and company_profile.company_name:
                company_name = company_profile.company_name
            else:
                company_name = (
                    job.company.get_full_name()
                    or job.company.username
                )

            recommended_jobs.append({
                "job": job,
                "match_percentage": 0.0,
                "company_name": company_name,
            })

    if selected_sort == "newest":
        recommended_jobs.sort(
            key=lambda item: item["job"].posted_at,
            reverse=True,
        )
    else:
        recommended_jobs.sort(
            key=lambda item: item["match_percentage"],
            reverse=True,
        )

    context = {
        "resume": resume,
        "recommended_jobs": recommended_jobs,
        "jobs_count": len(recommended_jobs),
        "search_query": search_query,
        "selected_location": selected_location,
        "selected_type": selected_type,
        "selected_sort": selected_sort,
        "employment_types": employment_types,
    }

    return render(
        request,
        "accounts/job_recommendations.html",
        context,
    )
