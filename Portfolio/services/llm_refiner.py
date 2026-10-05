# pyrefly: ignore [missing-import]
import google.generativeai as genai
import json

def refine_portfolio_data(raw_data_dict):
    """
    Takes the raw extracted dictionary, sends it to Gemini 1.5 Flash, 
    and asks it to return a polished JSON version.
    """
    # We use gemini-3.6-flash because it is extremely fast and cheap/free
    model = genai.GenerativeModel('gemini-3.6-flash')
    
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
- Each degree/qualification must be one array element.
- Preserve institution names and dates.
- Make each entry concise and professional.

EXPERIENCE:
- Separate every distinct company/job/position into its own array element.
- Do NOT combine different jobs into one item.
- Preserve company names, job titles, and employment dates.
- Rewrite descriptions professionally and action-oriented.
- If multiple responsibilities belong to the same job, keep them together within that job entry.

PROJECTS:
- Separate every distinct project into its own array element.
- Preserve project names and technologies.
- Rewrite descriptions professionally.
- Do NOT merge multiple projects into one item.

CERTIFICATIONS:
- Each certification must be a separate array element.
- Preserve certification name, issuing organization, and date if available.

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
- Every distinct item MUST be an object containing a 'heading' and 'body'.
- 'heading' should contain the title, company, or degree name.
- 'body' should contain the description, dates, and details.
- Example structure:
  "experience": [
      {{
          "heading": "Software Engineer at Google",
          "body": "Developed backend systems."
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
        response = model.generate_content(prompt)
        response_text = response.text.replace('```json', '').replace('```', '')
        polished_data = json.loads(response_text)
        return polished_data
    except Exception as e:
        # If the AI messes up or fails, fallback to the raw data
        print(f"Gemini API Error: {e}")
        return raw_data_dict

def verify_extracted_details(raw_data_dict, full_text):
    """
    Takes the raw extracted dictionary and the full parsed text, sends it to Gemini, 
    and asks it to verify and correct the details without changing the data structure.
    """
    model = genai.GenerativeModel('gemini-3.6-flash')
    
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
        response = model.generate_content(prompt)
        response_text = response.text.replace('```json', '').replace('```', '')
        verified_data = json.loads(response_text)
        return verified_data
    except Exception as e:
        print(f"Gemini API Error during verification: {e}")
        return raw_data_dict

