from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Resume
from .services.pdf_reader import extractText
from .services.resume_parse import *

def fetchingDetails(request):
    return render(request, "fetchingDetails.html")

def uploadResume(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to upload your resume")
        return redirect("userLogin")
    if request.method=="POST":
        resume=request.FILES["resume"]
        user=request.user
        resume_obj=Resume.objects.create(user=user,resume=resume)
        text=extractText(resume_obj.resume.path)

        resume_score = calculateResumeScore(text)
        if resume_score < 55:
            resume_obj.delete()
            messages.error(request, f"The uploaded document does not appear to be a valid resume. Please upload a proper resume file.")
            return redirect("uploadResume")

        email=extractEmail(text)
        phone=extractPhone(text)
        linkedin=extractLinkedIn(text)
        github=extractGithub(text)
        name=extractName(text)
        education=extractEducation(text)

        # Store extracted data in session to pass to the next view
        request.session['extracted_details'] = {
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
            "name": name,
            "education":education
        }
        return redirect("fetchingDetails")        
    return render(request,"uploadResume.html")

def editDetails(request):
    if not request.user.is_authenticated:
        return redirect("userLogin")
        
    if request.method == "POST":
        # Handle the form submission (saving edited details to DB)
        # For now we'll just redirect to home
        messages.success(request, "Portfolio generated successfully!")
        return redirect("index")
        
    details = request.session.get('extracted_details', {})
    return render(request, "extractedText.html", details)