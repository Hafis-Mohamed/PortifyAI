# pyrefly: ignore [missing-import]
import google.generativeai as genai
import json
import os
import re
import requests
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

def sanitize_portfolio_fields(data):
    """
    Cleans up dates that might have been mistakenly placed inside description paragraphs (body),
    extracting them into the 'year' field and keeping 'body' as a clean narrative.
    """
    if not isinstance(data, dict):
        return data

    date_prefix_regex = re.compile(
        r"^(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+)?\d{4}(?:\s*[\-–—to/]+\s*(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+)?(?:\d{4}|Present|Current))?\s*\|\s*",
        re.IGNORECASE
    )

    for field in ['projects', 'experience', 'education', 'certifications']:
        items = data.get(field, [])
        if isinstance(items, list):
            cleaned_items = []
            for item in items:
                if isinstance(item, dict):
                    body = item.get('body', '')
                    if isinstance(body, str):
                        match = date_prefix_regex.match(body.strip())
                        if match:
                            date_str = match.group(0).strip(" |–—-\t\r\n")
                            clean_body = body.strip()[match.end():].strip()
                            item['body'] = clean_body
                            if not item.get('year') or item.get('year') == 'Recent':
                                item['year'] = date_str
                    cleaned_items.append(item)
                else:
                    cleaned_items.append(item)
            data[field] = cleaned_items

    return data

def configure_gemini():
    load_dotenv(override=True)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        api_key = api_key.strip().strip("'\"")
        # transport='rest' ensures stable HTTPS communication instead of hanging gRPC sockets on Windows
        genai.configure(api_key=api_key, transport='rest')

def get_gemini_response(prompt):
    configure_gemini()
    # Verified active models for this API key and version
    models_to_try = [
        'gemini-3.8-flash',
        'gemini-3.5-flash',
        'gemini-3.5-flash-lite',
        'models/gemini-3.8-flash',
        'models/gemini-3.5-flash'
    ]
    last_err = None
    for m in models_to_try:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"Gemini model {m} attempt: {e}")
            last_err = e
            continue
    raise last_err or Exception("All Gemini models failed to generate content.")

def get_groq_response(prompt):
    load_dotenv(override=True)
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    api_key = api_key.strip().strip("'\"")
    models = ['openai/gpt-oss-120b', 'qwen/qwen3.8-27b', 'openai/gpt-oss-20b']
    for m in models:
        try:
            r = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={
                    'model': m,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.2
                },
                timeout=25
            )
            if r.status_code == 200:
                data = r.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content')
                if content:
                    return content
            else:
                print(f"Groq model {m} attempt ({r.status_code}): {r.text[:100]}")
        except Exception as e:
            print(f"Groq model {m} exception: {e}")
            continue
    return None

def get_ai_response(prompt):
    """
    First attempts Groq (ultra fast, high rate limits: 30 RPM).
    Falls back cleanly to Google Gemini.
    """
    try:
        groq_resp = get_groq_response(prompt)
        if groq_resp:
            return groq_resp
    except Exception as e:
        print(f"Groq attempt failed: {e}")
    
    return get_gemini_response(prompt)

def parse_llm_json(response_text):
    text = response_text.strip()
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()
    
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
        
    return json.loads(text)

def refine_portfolio_data(raw_data_dict):
    """
    Takes the raw extracted dictionary, sends it to Gemini (3.5 / 3.8 / Flash), 
    and asks it to return a polished JSON version.
    """
    # We instruct the AI exactly how to behave
    prompt = f"""
You are an expert resume parser, resume writer, and portfolio content structuring AI.

I will provide you with raw data extracted from a user's resume.

Your task has TWO goals:

1. STRUCTURE the extracted information correctly.
2. POLISH the wording so it is professional, concise, and suitable for a personal portfolio website.

IMPORTANT:
Do NOT invent, assume, or add information that is not present in the input.
Preserve all factual information such as names, dates, organizations, degrees, job titles, technologies, links, certifications, etc.

==================================================
IMPORTANT STRUCTURING RULE
==================================================

The extracted resume data may contain multiple pieces of information merged together into one string.

You MUST identify and separate each DISTINCT item into its own array element.

For example:

Input:
"education": [
    "MCA College of Engineering Trivandrum 2025-2027 BCA ABC College 2022-2025"
]

Output:
"education": [
    {{
        "heading": "MCA — College of Engineering Trivandrum",
        "body": "2025-2027"
    }},
    {{
        "heading": "BCA — ABC College",
        "body": "2022-2025"
    }}
]

Each education qualification must be a separate array element.

Do the same for ALL fields where multiple distinct items are present.

==================================================
FIELD-SPECIFIC RULES
==================================================

EDUCATION:
- Separate every distinct degree, diploma, school qualification, or academic qualification.
- 'heading': Degree and Institution (e.g. 'MCA — College of Engineering Trivandrum').
- 'year': Academic timeframe (e.g. '2025 - 2027').
- 'body': Relevant coursework, honors, or duration.
- Make each entry concise and professional.

EXPERIENCE:
- Separate every distinct company/job/position into its own array element.
- 'heading': Job Title and Company Name (e.g. 'Flutter Developer at Tech Solutions').
- 'year': Employment duration (e.g. '2024 - Present' or 'Dec 2024 - Apr 2025').
- 'body': Professional description of responsibilities and achievements.
- STRICT PROHIBITION: NEVER prepend dates or timelines to the 'body' paragraph (NEVER write '2024 | ...').
- Do NOT combine different jobs into one item.

PROJECTS:
- Separate every distinct project into its own array element.
- 'heading': Clean Project Title (e.g. 'Small Business Management System').
- 'year': Project release year, month/year, or timeframe (e.g. '2026' or 'April 2026'). If no date found, set to ''.
- 'body': Clear, professional description of the project features, backend, frontend, and impact.
- STRICT PROHIBITION: NEVER include or prepend dates or timelines inside the 'body' paragraph (NEVER write 'April 2026 | Currently developing...'). The 'body' must begin immediately with the narrative description.
- Do NOT merge multiple projects into one item.

CERTIFICATIONS:
- Each certification must be a separate array element.
- Preserve certification name, issuing organization, and date in 'year' if available.

SKILLS:
- Keep individual skills as separate array elements.
- Do not create skills that are not present in the original data.
- Remove obvious duplicates.

ACHIEVEMENTS:
- Each distinct achievement must be a separate array element.
- Keep factual information unchanged.

PUBLICATIONS:
- Each publication must be a separate array element.
- Preserve title, journal/conference, and dates if available.

VOLUNTEER:
- Each distinct volunteering experience must be a separate array element.
- Preserve organization and role information.

INTERESTS:
- Keep each distinct interest as a separate array element.

LANGUAGES:
- Keep each language as a separate object.
- Preserve the proficiency level.

SUMMARY:
- Rewrite the summary into a professional portfolio-ready paragraph.
- Keep it concise.
- Do not add qualifications, experience, skills, or achievements that are not present.

ROLE:
- Make the role/title professional and concise.
- Do not invent a role.

LOCATION:
- Identify the core location (City, State/Country).
- Format it cleanly (e.g. 'Trivandrum, Kerala, India').
- Do not include full street addresses or zip codes.

OTHER_LINKS:
- Preserve all generic links that are not GitHub or LinkedIn.

EMAIL:
- Extract the email address exactly.

PHONE:
- Extract the phone number. Format it cleanly.

GITHUB:
- Extract the GitHub profile URL. If absent, leave blank.

LINKEDIN:
- Extract the LinkedIn profile URL. If absent, leave blank.

NAME:
- Preserve the person's name exactly.

==================================================
VERY IMPORTANT OUTPUT REQUIREMENTS
==================================================

Return ONLY valid JSON.

Do NOT return:
- Markdown
- ```json
- Explanations
- Comments
- Extra text

The JSON MUST contain exactly these keys:

{{
    "name": "",
    "role": "",
    "location": "",
    "email": "",
    "phone": "",
    "github": "",
    "linkedin": "",
    "summary": "",
    "other_links": "",
    "education": [],
    "experience": [],
    "projects": [],
    "certifications": [],
    "skills": [],
    "interests": [],
    "achievements": [],
    "publications": [],
    "volunteer": [],
    "languages": []
}}

For array fields ('education', 'experience', 'projects', 'certifications'):
- Every distinct item MUST be an object containing 'heading', 'year', and 'body'.
- 'heading': Title, company, degree, or project name.
- 'year': Date, year, or duration (e.g. '2026', 'April 2026', '2024 - Present'). NEVER put this into 'body'.
- 'body': The description paragraph ONLY. Must NEVER contain date prefixes like 'April 2026 |'.
- Example structure:
  "projects": [
      {{
          "heading": "Small Business Management System",
          "year": "2026",
          "body": "Developing a Flutter application with Firebase backend to automate sales, expense tracking, and daily transactions. Features real-time synchronization and secure authentication."
      }}
  ],
  "experience": [
      {{
          "heading": "Software Engineer at Google",
          "year": "2024 - Present",
          "body": "Architected cloud microservices to handle high-concurrency requests."
      }}
  ]

For 'skills':
- Group skills into logical categories (e.g. Programming Languages, Frameworks, Tools).
- Each distinct category MUST be an object with 'category' and 'items'.
- Example structure:
  "skills": [
      {{
          "category": "Programming Languages",
          "items": ["Python", "JavaScript", "C++"]
      }}
  ]

For simple array fields ('interests', 'achievements', 'publications', 'volunteer'):
- These can remain simple strings unless they naturally fit a heading/body structure.
- Never put multiple unrelated resume items into one array element.
- Do not create empty elements.

For languages use this structure:

"languages": [
    {{
        "name": "English",
        "proficiency": "Fluent"
    }},
    {{
        "name": "Hindi",
        "proficiency": "Intermediate"
    }}
]

==================================================
RAW RESUME DATA
==================================================

{json.dumps(raw_data_dict, ensure_ascii=False)}

==================================================
FINAL INSTRUCTION
==================================================

Analyze the raw data carefully, identify the boundaries between distinct resume entries, split them into separate array elements, then professionally rewrite the content while preserving the original facts.

Return ONLY the JSON object.
"""
    # Call the API and parse the response inside a try/except block
    # so we fallback safely if the API key is wrong or rate limited
    try:
        response_text = get_ai_response(prompt)
        polished_data = parse_llm_json(response_text)
        return sanitize_portfolio_fields(polished_data)
    except Exception as e:
        # If the AI messes up or fails, fallback to the raw data
        print(f"AI API Error: {e}")
        return sanitize_portfolio_fields(raw_data_dict)

def verify_extracted_details(raw_data_dict, full_text):
    """
    Takes the raw extracted dictionary and the full parsed text, sends it to Gemini (3.5 / 3.8 / Flash), 
    and asks it to verify and correct the details without changing the data structure.
    """
    prompt = f"""
You are an expert resume parser and data verification AI.

I will provide you with raw data extracted from a user's resume, along with the full parsed text of the resume.
Your task is to VERIFY the extracted information and CORRECT any mistakes or missing information based on the full text.

IMPORTANT RULES:
1. Do NOT invent, assume, or add information that is not present in the full text.
2. The output MUST maintain the exact same JSON structure as the input (arrays of strings for sections like education, experience, etc.).
3. Do NOT convert arrays of strings into arrays of objects with 'heading' and 'body'. Keep them as simple arrays of strings.
4. Clean up any weird formatting, newline characters, or OCR errors.
5. If a section was completely missed in the raw extraction but exists in the full text, add it to the appropriate array.

==================================================
FULL RESUME TEXT
==================================================
{full_text}

==================================================
RAW EXTRACTED DATA
==================================================
{json.dumps(raw_data_dict, ensure_ascii=False)}

Return ONLY the corrected JSON object.
"""
    try:
        response_text = get_ai_response(prompt)
        verified_data = parse_llm_json(response_text)
        return verified_data
    except Exception as e:
        print(f"AI API Error during verification: {e}")
        return raw_data_dict


