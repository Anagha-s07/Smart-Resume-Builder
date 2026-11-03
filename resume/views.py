
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string

from accounts.models import UserProfile
from .models import Resume, Job, Application
from .forms import ResumeForm, JobForm


# CREATE RESUME
@login_required
def create_resume(request):
    if request.method == "POST":
        form = ResumeForm(request.POST)

        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()

            messages.success(request, "Resume created successfully.")
            return redirect("template_selection", resume_id=resume.id)
    else:
        form = ResumeForm()

    return render(request, "resume/create_resume.html", {"form": form})


# EDIT RESUME
@login_required
def edit_resume(request, resume_id):
    resume = get_object_or_404(
        Resume, id=resume_id, user=request.user
    )

    if request.method == "POST":
        form = ResumeForm(request.POST, instance=resume)

        if form.is_valid():
            form.save()
            messages.success(request, "Resume updated successfully.")
            return redirect("template_selection", resume_id=resume.id)
    else:
        form = ResumeForm(instance=resume)

    return render(
        request,
        "resume/create_resume.html",
        {"form": form, "resume": resume, "editing": True},
    )


# SELECT A RESUME DESIGN
@login_required
def template_selection(request, resume_id):
    resume = get_object_or_404(
        Resume, id=resume_id, user=request.user
    )

    return render(
        request,
        "resume/template_selection.html",
        {"resume": resume, "resume_id": resume.id},
    )


# PREVIEW RESUME
@login_required
def resume_preview(request, resume_id, template):
    resume = get_object_or_404(
        Resume, id=resume_id, user=request.user
    )

    allowed_templates = [
        "modern", "minimalist", "creative", "executive", "ats"
    ]

    if template not in allowed_templates:
        messages.error(request, "Invalid resume template.")
        return redirect("template_selection", resume_id=resume.id)

    return render(
        request,
        f"resume/{template}.html",
        {
            "resume": resume,
            "template": template,
            "resume_id": resume.id,
        },
    )


# DOWNLOAD RESUME AS PDF
@login_required
def download_resume_pdf(request, resume_id, template):
    from xhtml2pdf import pisa

    resume = get_object_or_404(
        Resume, id=resume_id, user=request.user
    )

    allowed_templates = [
        "modern", "minimalist", "creative", "executive", "ats"
    ]

    if template not in allowed_templates:
        return HttpResponse("Invalid resume template.", status=400)

    html = render_to_string(
        f"resume/{template}.html",
        {
            "resume": resume,
            "template": template,
            "resume_id": resume.id,
        },
        request=request,
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="resume_{resume.id}_{template}.pdf"'
    )

    pdf_status = pisa.CreatePDF(html, dest=response)

    if pdf_status.err:
        return HttpResponse(
            "There was an error generating the PDF. Please try again.",
            status=500,
        )

    return response


# POST A JOB
@login_required
def post_job(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile first.")
        return redirect("dashboard")

    if profile.role != "company":
        return redirect("dashboard")

    if request.method == "POST":
        form = JobForm(request.POST)

        if form.is_valid():
            job = form.save(commit=False)
            job.company = request.user
            job.save()
            messages.success(request, "Job posted successfully.")
            return redirect("manage_jobs")
    else:
        form = JobForm()

    return render(request, "resume/post_job.html", {"form": form})


# JOB DETAILS
@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    try:
        profile = UserProfile.objects.get(user=request.user)
        is_company = profile.role == "company"
    except UserProfile.DoesNotExist:
        is_company = False

    already_applied = Application.objects.filter(
        job=job, applicant=request.user
    ).exists()

    return render(
        request,
        "resume/job_detail.html",
        {
            "job": job,
            "already_applied": already_applied,
            "is_company": is_company,
        },
    )


# APPLY FOR A JOB
@login_required
def apply_job(request, job_id):
    if request.method != "POST":
        return redirect("job_detail", job_id=job_id)

    job = get_object_or_404(Job, id=job_id, is_active=True)

    if job.company == request.user:
        messages.error(request, "You cannot apply for your own job.")
        return redirect("job_detail", job_id=job.id)

    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "Your user profile could not be found.")
        return redirect("dashboard")

    if profile.role != "user":
        messages.error(request, "Only job seekers can apply for jobs.")
        return redirect("job_detail", job_id=job.id)

    application, created = Application.objects.get_or_create(
        job=job, applicant=request.user
    )

    if created:
        messages.success(request, "Your application was submitted.")
    else:
        messages.info(request, "You have already applied for this job.")

    return redirect("job_detail", job_id=job.id)


# MANAGE COMPANY JOBS
@login_required
def manage_jobs(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role != "company":
        return redirect("dashboard")

    jobs = Job.objects.filter(company=request.user).order_by("-posted_at")
    total_jobs = jobs.count()
    active_jobs = jobs.filter(is_active=True).count()

    return render(
        request,
        "resume/manage_jobs.html",
        {
            "profile": profile,
            "jobs": jobs,
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "closed_jobs": total_jobs - active_jobs,
        },
    )


# CLOSE OR REOPEN A JOB
@login_required
def toggle_job_status(request, job_id):
    if request.method != "POST":
        return redirect("manage_jobs")

    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role != "company":
        return redirect("dashboard")

    job = get_object_or_404(
        Job, id=job_id, company=request.user
    )
    job.is_active = not job.is_active
    job.save(update_fields=["is_active"])

    messages.success(request, "Job status updated successfully.")
    return redirect("manage_jobs")


# DELETE A JOB
@login_required
def delete_job(request, job_id):
    if request.method != "POST":
        return redirect("manage_jobs")

    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role != "company":
        return redirect("dashboard")

    job = get_object_or_404(
        Job, id=job_id, company=request.user
    )
    job.delete()

    messages.success(request, "Job deleted successfully.")
    return redirect("manage_jobs")
