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

