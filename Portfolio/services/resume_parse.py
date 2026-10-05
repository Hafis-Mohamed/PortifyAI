# pyrefly: ignore [missing-import]
import re, spacy, string

nlp=spacy.load("en_core_web_sm")

def clean_heading(line):
    cleaned = line.encode('ascii', 'ignore').decode('ascii')
    return cleaned.lower().strip(string.punctuation + " \t")

#EXTRACT EMAIL FROM THE RESUME
def extractEmail(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match=re.search(pattern,text)
    if match:
        return match.group()
    return None

#EXTRACT PHONE NUMBER FROM THE RESUME
def extractPhone(text):
    pattern = r'(\+?\d[\d\s\-]{8,}\d)'
    match=re.search(pattern,text)
    if match:
        return match.group()
    return None

#EXTRACT LINKEDIN LINK FROM THE RESUME
def extractLinkedIn(text):
    pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/\S+'
    match=re.search(pattern,text)
    if match:
        return match.group()
    return None

#EXTRACT GITHUB LINK FROM THE RESUME
def extractGithub(text):
    pattern = r'(?:https?://)?(?:www\.)?github\.com/\S+'
    match=re.search(pattern,text)
    if match:
        return match.group()
    return None

#EXTRACT NAME FROM THE RESUME
def extractName(text):
    # 1. Fallback heuristic (often more accurate because name is at the top)
    lines = text.split("\n")
    for line in lines[:10]:
        line = line.strip()
        if not line:
            continue
        if "resume" in line.lower() or "cv" in line.lower() or "curriculum vitae" in line.lower():
            continue
        if "@" in line or "http" in line.lower() or "www" in line.lower():
            continue
        if "linkedin" in line.lower() or "github" in line.lower():
            continue
        if re.search(r"\d", line):
            continue
        
        words = line.split()
        if 1 < len(words) <= 4:
            valid = True
            for word in words:
                if not word.replace(".", "").replace("-", "").isalpha():
                    valid = False
                    break
            if valid:
                return line

    # 2. Try using spaCy if heuristic misses it
    doc = nlp(text[:1000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            clean_name = re.sub(r'\s+', ' ', ent.text).strip()
            if 1 < len(clean_name.split()) <= 4:
                if clean_name.replace(".", "").replace("-", "").replace(" ", "").isalpha():
                    return clean_name
                    
    return None

#EXTRACT PROFESSIONAL ROLE FROM THE RESUME
def extractRole(text):
    roles = [
        "software engineer", "software developer", "full stack developer", "full-stack developer",
        "frontend developer", "front-end developer", "backend developer", "back-end developer",
        "web developer", "java developer", "python developer", "c++ developer", "react developer",
        "data scientist", "data analyst", "machine learning engineer", "ai engineer", "data engineer",
        "devops engineer", "cloud engineer", "system administrator", "network engineer",
        "ui/ux designer", "ui designer", "ux designer", "product designer", "graphic designer",
        "product manager", "project manager", "business analyst", "quality assurance",
        "qa tester", "qa engineer", "mobile developer", "ios developer", "android developer",
        "game developer", "blockchain developer", "cybersecurity analyst", "security engineer"
    ]
    
    # Try to find the role in the first 20 lines to ensure it's their actual title
    # rather than just a mention in their experience
    lines = text.split("\n")
    for line in lines[:20]:
        lower_line = line.lower()
        for role in roles:
            # Check if role is present as a standalone phrase or within the line
            if role in lower_line:
                # Find the original case from the line if possible, or just title case the role
                import re
                match = re.search(re.escape(role), line, re.IGNORECASE)
                if match:
                    return match.group(0).title()
                return role.title()
                
    return None

#EXTRACT LOCATION FROM THE RESUME
def extractLocation(text):
    lines = text.split("\n")
    for line in lines[:15]:
        line = line.strip()
        
        # Remove emails and urls from line before checking
        line = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', line)
        line = re.sub(r'(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/\S+', '', line)
        # Remove phone numbers
        line = re.sub(r'\+?\d[\d\s\-]{8,}\d', '', line)
        
        if len(line.strip()) < 3:
            continue
            
        doc = nlp(line)
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                clean = re.sub(r'\s+', ' ', ent.text).strip()
                # Basic validation: length > 2 and no numbers
                if len(clean) > 2 and not any(char.isdigit() for char in clean):
                    return clean
    return None

# UNIFIED HEADINGS LIST FOR ALL SECTIONS TO STOP CAPTURING
ALL_SECTION_HEADINGS = [
    "education", "academic qualification", "academic qualifications", "qualification", "qualifications", "education & qualifications",
    "projects", "personal projects", "academic projects", "key projects", "major projects", "software projects",
    "certifications", "certification", "licenses & certifications", "certificates", "courses & certifications",
    "experience", "work experience", "professional experience", "employment history", "work history", "internship", "internships", "career history", "roles & responsibilities", "roles and responsibilities", "responsibilities",
    "skills", "technical skills", "soft skills", "interpersonal skills", "professional skills", "key skills", "core competencies", "technologies", "expertise", "it skills",
    "languages", "spoken languages", "known languages",
    "interests", "hobbies", "hobbies & interests", "interests & hobbies", "extracurricular activities", "extracurriculars",
    "achievements", "awards", "honors", "awards & honors", "honors & awards", "accomplishments",
    "profile", "summary", "contact", "objective", "about me", "professional summary", "career objective", "personal profile",
    "publications", "research", "research & publications", "patents", "publications & patents",
    "volunteer", "volunteer experience", "volunteering", "community service", "social work", "social causes"
]

#EXTRACT EDUCATION FROM THE RESUME
EDUCATION_HEADINGS = [
    "education",
    "academic qualification",
    "academic qualifications",
    "qualification",
    "qualifications",
    "education & qualifications"
]
def extractEducation(text):
    lines = text.split("\n")

    raw_edu_lines = []
    capture = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        lower = clean_heading(line)
        if any(h == lower for h in EDUCATION_HEADINGS):
            capture = True
            continue

        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in EDUCATION_HEADINGS:
                break
            raw_edu_lines.append(line)

    if raw_edu_lines:
        return ["\n".join(raw_edu_lines)]
    return []

#EXTRACT PROJECTS FROM THE RESUME
PROJECTS_HEADINGS = [
    "projects",
    "personal projects",
    "academic projects",
    "key projects",
    "major projects",
    "software projects"
]

def extractProjects(text):
    lines = text.split("\n")

    raw_project_lines = []
    capture = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        lower = clean_heading(line)
        if any(h == lower for h in PROJECTS_HEADINGS):
            capture = True
            continue

        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in PROJECTS_HEADINGS:
                break
            raw_project_lines.append(line)

    if raw_project_lines:
        return ["\n".join(raw_project_lines)]
    return []

#EXTRACT CERTIFICATIONS FROM THE RESUME
CERTIFICATIONS_HEADINGS = [
    "certifications",
    "certification",
    "licenses & certifications",
    "certificates",
    "courses & certifications"
]

def extractCertifications(text):
    lines = text.split("\n")

    raw_cert_lines = []
    capture = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        lower = clean_heading(line)
        if any(h == lower for h in CERTIFICATIONS_HEADINGS):
            capture = True
            continue

        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in CERTIFICATIONS_HEADINGS:
                break
            raw_cert_lines.append(line)

    if raw_cert_lines:
        return ["\n".join(raw_cert_lines)]
    return []

#EXTRACT WORK EXPERIENCE FROM THE RESUME
EXPERIENCE_HEADINGS = [
    "experience",
    "work experience",
    "professional experience",
    "employment history",
    "work history",
    "internship",
    "internships",
    "career history"
]

def extractExperience(text):
    lines = text.split("\n")

    raw_exp_lines = []
    capture = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        lower = clean_heading(line)
        if any(h == lower for h in EXPERIENCE_HEADINGS):
            capture = True
            continue

        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in EXPERIENCE_HEADINGS:
                break
            raw_exp_lines.append(line)

    if raw_exp_lines:
        return ["\n".join(raw_exp_lines)]
    return []

#EXTRACT SKILLS FROM THE RESUME
SKILLS_HEADINGS = [
    "skills",
    "technical skills",
    "soft skills",
    "interpersonal skills",
    "professional skills",
    "key skills",
    "core competencies",
    "technologies",
    "expertise",
    "it skills"
]

def extractSkills(text):
    lines = text.split("\n")
    raw_skills = []
    capture = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        lower = clean_heading(line)
        if any(h == lower for h in SKILLS_HEADINGS):
            capture = True
            continue

        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in SKILLS_HEADINGS:
                break
            raw_skills.append(line)

    if raw_skills:
        return ["\n".join(raw_skills)]
    return []

#EXTRACTS LANGUAGES FROM THE RESUME
LANGUAGES_HEADINGS = [
    "languages",
    "spoken languages",
    "known languages"
]

def extractLanguages(text):
    lines = text.split("\n")
    raw_lang_lines = []
    capture = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        lower = clean_heading(line)
        if any(h == lower for h in LANGUAGES_HEADINGS):
            capture = True
            continue

        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in LANGUAGES_HEADINGS:
                break
            raw_lang_lines.append(line)

    common_langs = [
        "english", "spanish", "french", "german", "mandarin", "chinese", "hindi", "arabic", 
        "portuguese", "bengali", "russian", "japanese", "punjabi", "marathi", "telugu", "turkish", 
        "korean", "vietnamese", "tamil", "urdu", "italian", "gujarati", "persian", "kannada", 
        "indonesian", "polish", "malayalam", "dutch", "greek", "swedish", "danish", "finnish"
    ]
    
    found_langs = set()

    if raw_lang_lines:
        combined_text = " ".join(raw_lang_lines)
        words = re.findall(r'[a-zA-Z]+', combined_text)
        for word in words:
            if word.lower() in common_langs:
                found_langs.add(word.title())
                
        # if we didn't find specific ones but have text in the section, just return the raw text split by commas
        if not found_langs and combined_text.strip():
            items = re.split(r'[,|•\n]', combined_text)
            return [item.strip() for item in items if item.strip()]

        if found_langs:
            return list(found_langs)
            
    # If no section was found, or section had no specific language names,
    # scan the entire text for common languages as a robust fallback
    words = re.findall(r'[a-zA-Z]+', text)
    for word in words:
        if word.lower() in common_langs:
            found_langs.add(word.title())
            
    return list(found_langs)

#EXTRACT INTERESTS AND HOBBIES FROM THE RESUME
INTERESTS_HEADINGS = [
    "interests",
    "hobbies",
    "hobbies & interests",
    "interests & hobbies",
    "extracurricular activities",
    "extracurriculars"
]

def extractInterests(text):
    lines = text.split("\n")
    raw_interest_lines = []
    capture = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        lower = clean_heading(line)
        if any(h == lower for h in INTERESTS_HEADINGS):
            capture = True
            continue

        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in INTERESTS_HEADINGS:
                break
            raw_interest_lines.append(line)

    if raw_interest_lines:
        return ["\n".join(raw_interest_lines)]
    return []

#EXTRACT ACHIEVEMENTS FROM THE RESUME
ACHIEVEMENTS_HEADINGS = [
    "achievements",
    "awards",
    "honors",
    "awards & honors",
    "honors & awards",
    "accomplishments"
]
def extractAchievements(text):
    lines = text.split("\n")
    raw_lines = []
    capture = False
    for line in lines:
        line = line.strip()
        if not line: continue
        lower = clean_heading(line)
        if any(h == lower for h in ACHIEVEMENTS_HEADINGS):
            capture = True
            continue
        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in ACHIEVEMENTS_HEADINGS:
                break
            raw_lines.append(line)
    if raw_lines:
        return ["\n".join(raw_lines)]
    return []

#EXTRACT SUMMARY FROM THE RESUME
SUMMARY_HEADINGS = [
    "summary",
    "profile",
    "objective",
    "about me",
    "professional summary",
    "career objective",
    "personal profile"
]
def extractSummary(text):
    lines = text.split("\n")
    raw_lines = []
    capture = False
    for line in lines:
        line = line.strip()
        if not line: continue
        lower = clean_heading(line)
        if any(h == lower for h in SUMMARY_HEADINGS):
            capture = True
            continue
        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in SUMMARY_HEADINGS:
                break
            raw_lines.append(line)
    if raw_lines:
        return "\n".join(raw_lines)
    return ""

#EXTRACT PUBLICATIONS FROM THE RESUME
PUBLICATIONS_HEADINGS = [
    "publications",
    "research",
    "research & publications",
    "patents",
    "publications & patents"
]
def extractPublications(text):
    lines = text.split("\n")
    raw_lines = []
    capture = False
    for line in lines:
        line = line.strip()
        if not line: continue
        lower = clean_heading(line)
        if any(h == lower for h in PUBLICATIONS_HEADINGS):
            capture = True
            continue
        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in PUBLICATIONS_HEADINGS:
                break
            raw_lines.append(line)
    if raw_lines:
        return ["\n".join(raw_lines)]
    return []

#EXTRACT VOLUNTEER EXPERIENCE FROM THE RESUME
VOLUNTEER_HEADINGS = [
    "volunteer",
    "volunteer experience",
    "volunteering",
    "community service",
    "social work",
    "social causes",
    "roles & responsibilities",
    "roles and responsibilities",
    "responsibilities"
]
def extractVolunteer(text):
    lines = text.split("\n")
    raw_lines = []
    capture = False
    for line in lines:
        line = line.strip()
        if not line: continue
        lower = clean_heading(line)
        if any(h == lower for h in VOLUNTEER_HEADINGS):
            capture = True
            continue
        if capture:
            if lower in ALL_SECTION_HEADINGS and lower not in VOLUNTEER_HEADINGS:
                break
            raw_lines.append(line)
    if raw_lines:
        return ["\n".join(raw_lines)]
    return []

#EXTRACT OTHER LINKS FROM THE RESUME
def extractOtherLinks(text):
    pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    matches = re.findall(pattern, text)
    
    other_links = set()
    for link in matches:
        # Remove common trailing punctuation often caught by regex
        link = link.rstrip('.,;)')
        lower_link = link.lower()
        if "linkedin.com" not in lower_link and "github.com" not in lower_link:
            other_links.add(link)
            
    return "\n".join(other_links)

#TO FIND WHETHER THE UPLOADED DOCUMENT IS RESUME OR NOT 
def calculateResumeScore(text):
    score = 0
    text_lower = text.lower()

    if extractEmail(text):
        score += 20
    if extractPhone(text):
        score += 20

    if extractLinkedIn(text):
        score += 10
    if extractGithub(text):
        score += 10

    education_keywords = ["education", "academic", "university", "college", "degree", "bachelor", "master", "cgpa", "gpa"]
    if any(keyword in text_lower for keyword in education_keywords):
        score += 15

    experience_keywords = ["experience", "work", "employment", "internship", "role"]
    if any(keyword in text_lower for keyword in experience_keywords):
        score += 15

    skills_keywords = ["skills", "technologies", "tools", "projects", "certifications", "portfolio"]
    if any(keyword in text_lower for keyword in skills_keywords):
        score += 10

    return min(score, 100)
