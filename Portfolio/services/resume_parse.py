# pyrefly: ignore [missing-import]
import re,spacy
from pyresparser import ResumeParser

nlp=spacy.load("en_core_web_sm")

def extractEmail(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match=re.search(pattern,text)
    if match:
        return match.group()
    return None

def extractPhone(text):
    pattern = r'(\+?\d[\d\s\-]{8,}\d)'
    match=re.search(pattern,text)
    if match:
        return match.group()
    return None

def extractLinkedIn(text):
    pattern = r'https?://(?:www\.)?linkedin\.com/\S+'
    match=re.search(pattern,text)
    if match:
        return match.group()
    return None

def extractGithub(text):
    pattern = r'https?://(?:www\.)?github\.com/\S+'
    match=re.search(pattern,text)
    if match:
        return match.group()
    return None

import re

def extractName(text):
    lines = text.split("\n")

    # Check only the first 10 lines
    for line in lines[:10]:
        line = line.strip()
        if not line:
            continue
        # Skip emails
        if "@" in line:
            continue
        # Skip URLs
        if "http" in line.lower() or "www" in line.lower():
            continue
        # Skip LinkedIn/GitHub
        if "linkedin" in line.lower() or "github" in line.lower():
            continue
        # Skip lines containing numbers
        if re.search(r"\d", line):
            continue
        # Remove extra spaces
        words = line.split()
        # Name should usually contain 2-4 words
        if 2 <= len(words) <= 4:
            # Check every word contains only alphabets
            valid = True
            for word in words:
                if not word.replace(".", "").replace("-", "").isalpha():
                    valid = False
                    break
            if valid:
                return line
    return None


EDUCATION_HEADINGS = [
    "education",
    "academic qualification",
    "academic qualifications",
    "qualification",
    "qualifications",
    "education & qualifications"
]
NEXT_HEADINGS = [
    "skills",
    "projects",
    "experience",
    "work experience",
    "internship",
    "certifications",
    "achievements",
    "languages",
    "interests",
    "profile",
    "summary",
    "contact"
]
def extractEducation(text):
    lines = text.split("\n")

    education = []
    capture = False

    for line in lines:
        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        if any(h == lower for h in EDUCATION_HEADINGS):
            capture = True
            continue

        if capture:
            if any(h == lower for h in NEXT_HEADINGS):
                break

            education.append(line)

    return education


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
