from Portfolio.services.llm_refiner import refine_portfolio_data, verify_extracted_details
from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
import zipfile
import io
from django.contrib import messages
from .models import Resume, Portfolio, PortfolioURL
from .services.pdf_reader import extractText
from .services.resume_parse import *
from .services.vercel_deploy import deploy_to_vercel

def fetchingDetails(request):
    return render(request, "fetchingDetails.html")

def process_llm_extraction(request):
    if request.method == "POST":
        raw_details = request.session.get('extracted_details')
        raw_text = request.session.get('raw_text')
        if raw_details and raw_text:
            verified_data = verify_extracted_details(raw_details, raw_text)
            request.session['extracted_details'] = verified_data
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)

def uploadResume(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to upload your resume")
        return redirect("userLogin")
    if request.method=="POST":
        resume=request.FILES["resume"]
        user=request.user
        resume_obj=Resume.objects.create(user=user,resume=resume)
        text=extractText(resume_obj.resume.path)

        # Fix missing newlines common in PDF parsing (e.g. "design.LANGUAGES" -> "design.\nLANGUAGES")
        import re
        text = re.sub(r'([a-z][\.!?])([A-Z])', r'\1\n\2', text)

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
        role=extractRole(text)
        education=extractEducation(text)
        projects=extractProjects(text)
        certifications=extractCertifications(text)
        experience=extractExperience(text)
        skills=extractSkills(text)
        languages=extractLanguages(text)
        interests=extractInterests(text)
        achievements=extractAchievements(text)
        summary=extractSummary(text)
        location=extractLocation(text)
        publications=extractPublications(text)
        volunteer=extractVolunteer(text)
        other_links=extractOtherLinks(text)

        # Store extracted data in session to pass to the next view
        raw_details = {
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
            "name": name,
            "role": role,
            "education":education,
            "projects": projects,
            "certifications": certifications,
            "experience": experience,
            "skills": skills,
            "languages": languages,
            "interests": interests,
            "achievements": achievements,
            "summary": summary,
            "location": location,
            "publications": publications,
            "volunteer": volunteer,
            "other_links": other_links
        }
        request.session['extracted_details'] = raw_details
        request.session['raw_text'] = text
        return redirect("fetchingDetails")        
    return render(request,"uploadResume.html")

def editDetails(request):
    if not request.user.is_authenticated:
        return redirect("userLogin")
        
    if request.method == "POST":
        # Handle the form submission (saving edited details to DB)
        portfolio, created = Portfolio.objects.get_or_create(user=request.user)
        
        # Collect user-submitted data into a dictionary
        submitted_data = {
            "name": request.POST.get('name', ''),
            "role": request.POST.get('role', ''),
            "location": request.POST.get('location', ''),
            "email": request.POST.get('email', ''),
            "phone": request.POST.get('phone', ''),
            "github": request.POST.get('github', ''),
            "linkedin": request.POST.get('linkedin', ''),
            "summary": request.session.get('extracted_details', {}).get('summary', ''),
            "other_links": request.POST.get('other_links', ''),
            "education": [x for x in request.POST.getlist('education[]') if x.strip()],
            "experience": [x for x in request.POST.getlist('experience[]') if x.strip()],
            "projects": [x for x in request.POST.getlist('projects[]') if x.strip()],
            "certifications": [x for x in request.POST.getlist('certifications[]') if x.strip()],
            "skills": [x for x in request.POST.getlist('skills[]') if x.strip()],
            "interests": [x for x in request.POST.getlist('interests[]') if x.strip()],
            "achievements": [x for x in request.POST.getlist('achievements[]') if x.strip()],
            "publications": [x for x in request.POST.getlist('publications[]') if x.strip()],
            "volunteer": [x for x in request.POST.getlist('volunteer[]') if x.strip()]
        }
        
        # Languages parsing
        lang_names = request.POST.getlist('language_name[]')
        lang_profs = request.POST.getlist('language_proficiency[]')
        languages = []
        for n, p in zip(lang_names, lang_profs):
            if n.strip():
                languages.append({"name": n.strip(), "proficiency": p.strip()})
        submitted_data["languages"] = languages
        
        request.session['finalizing_data'] = submitted_data
        return redirect("generatingPortfolio")
        
    details = request.session.get('extracted_details', {})
    return render(request, "extractedText.html", details)

def generatingPortfolio(request):
    if not request.user.is_authenticated:
        return redirect("userLogin")
    return render(request, "generatingPortfolio.html")

def processPortfolio(request):
    if not request.user.is_authenticated:
        return redirect("userLogin")
        
    submitted_data = request.session.get('finalizing_data')
    if not submitted_data:
        return redirect("uploadResume")
        
    portfolio, created = Portfolio.objects.get_or_create(user=request.user)
    
    # Polish this finalized data using Gemini
    polished_data = refine_portfolio_data(submitted_data)
    
    # Save the polished data to the database
    portfolio.name = polished_data.get('name', submitted_data.get('name', ''))
    portfolio.role = polished_data.get('role', submitted_data.get('role', ''))
    portfolio.location = polished_data.get('location', submitted_data.get('location', ''))
    portfolio.email = polished_data.get('email', submitted_data.get('email', ''))
    portfolio.phone = polished_data.get('phone', submitted_data.get('phone', ''))
    portfolio.github = polished_data.get('github', submitted_data.get('github', ''))
    portfolio.linkedin = polished_data.get('linkedin', submitted_data.get('linkedin', ''))
    portfolio.summary = polished_data.get('summary', submitted_data.get('summary', ''))
    portfolio.other_links = polished_data.get('other_links', submitted_data.get('other_links', ''))
    portfolio.education = polished_data.get('education', submitted_data.get('education', []))
    portfolio.experience = polished_data.get('experience', submitted_data.get('experience', []))
    portfolio.projects = polished_data.get('projects', submitted_data.get('projects', []))
    portfolio.certifications = polished_data.get('certifications', submitted_data.get('certifications', []))
    portfolio.skills = polished_data.get('skills', submitted_data.get('skills', []))
    portfolio.interests = polished_data.get('interests', submitted_data.get('interests', []))
    portfolio.achievements = polished_data.get('achievements', submitted_data.get('achievements', []))
    portfolio.publications = polished_data.get('publications', submitted_data.get('publications', []))
    portfolio.volunteer = polished_data.get('volunteer', submitted_data.get('volunteer', []))
    portfolio.languages = polished_data.get('languages', submitted_data.get('languages', []))
    
    portfolio.save()
    
    # Clear the temporary session data
    if 'finalizing_data' in request.session:
        del request.session['finalizing_data']
        
    messages.success(request, "Details saved successfully! Choose your template.")
    return redirect("chooseTemplate")

def chooseTemplate(request):
    if not request.user.is_authenticated:
        return redirect("userLogin")
    return render(request, "chooseTemplate.html")

def previewPortfolio(request, template_id):
    if not request.user.is_authenticated:
        return redirect("userLogin")
    
    try:
        portfolio = Portfolio.objects.get(user=request.user)
    except Portfolio.DoesNotExist:
        messages.error(request, "Please submit your details first.")
        return redirect("uploadResume")
        
    # Render the chosen template (e.g., portfolio_template_1.html)
    template_name = f"{template_id}.html"
    return render(request, template_name, {"portfolio": portfolio})

def saveTemplateChoice(request):
    if not request.user.is_authenticated:
        return redirect("userLogin")
        
    if request.method == "POST":
        template_id = request.POST.get('template_id')
        if template_id:
            try:
                portfolio = Portfolio.objects.get(user=request.user)
                portfolio.template_choice = template_id
                portfolio.save()
                
                # Deploy to Vercel
                template_name = f"{template_id}.html"
                html_content = render_to_string(template_name, {"portfolio": portfolio, "is_export": True})
                project_name = f"portifyai-{request.user.username}"
                
                try:
                    live_url = deploy_to_vercel(html_content, project_name)
                    # Save the URL
                    portfolio_url, created = PortfolioURL.objects.get_or_create(user=request.user)
                    portfolio_url.url = live_url
                    portfolio_url.save()
                    return redirect("deploymentSuccess")
                except Exception as e:
                    messages.error(request, f"Deployment failed: {str(e)}")
                    return redirect("chooseTemplate")
                    
            except Portfolio.DoesNotExist:
                messages.error(request, "Portfolio not found.")
                return redirect("chooseTemplate")
                
    return redirect("chooseTemplate")

def deploymentSuccess(request):
    if not request.user.is_authenticated:
        return redirect("userLogin")
    try:
        portfolio_url = PortfolioURL.objects.get(user=request.user)
        return render(request, "deploymentSuccess.html", {"live_url": portfolio_url.url})
    except PortfolioURL.DoesNotExist:
        return redirect("chooseTemplate")

def download_portfolio_zip(request, template_id):
    if not request.user.is_authenticated:
        return redirect("userLogin")
        
    try:
        portfolio = Portfolio.objects.get(user=request.user)
    except Portfolio.DoesNotExist:
        messages.error(request, "Please submit your details first.")
        return redirect("uploadResume")
        
    template_name = f"{template_id}.html"
    
    # Render the HTML for export (passing is_export=True to hide preview bar)
    html_content = render_to_string(template_name, {"portfolio": portfolio, "is_export": True})
    
    # Create the ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("index.html", html_content)
        
    zip_buffer.seek(0)
    
    response = HttpResponse(zip_buffer, content_type="application/zip")
    response['Content-Disposition'] = f'attachment; filename={portfolio.name.replace(" ", "_")}_portfolio.zip'
    return response