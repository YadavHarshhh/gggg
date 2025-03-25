import os
import google.generativeai as genai
import PyPDF2
import docx
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

class ResumeProcessor:
    def __init__(self):
        # Initialize Gemini API
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer()

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None

    def extract_text_from_docx(self, docx_path):
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(docx_path)
            text = ''
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
            return text
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return None

    def analyze_resume_sync(self, file_path):
        """Analyze resume using Gemini API."""
        # Extract text based on file type
        if file_path.endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format")

        if not text:
            raise ValueError("Failed to extract text from resume")

        try:
            # Use Gemini to extract structured information
            prompt = f"""
            Analyze this resume and extract key information in the following JSON format:
            {{
                "skills": ["list of technical and soft skills"],
                "experience": [
                    {{
                        "title": "job title",
                        "company": "company name",
                        "period": "duration",
                        "responsibilities": ["key responsibilities"]
                    }}
                ],
                "education": [
                    {{
                        "degree": "degree name",
                        "institution": "institution name",
                        "year": "completion year"
                    }}
                ]
            }}

            Resume text:
            {text}
            """

            response = self.model.generate_content(prompt)
            
            # Parse the response
            try:
                analysis = json.loads(response.text)
            except json.JSONDecodeError:
                # Fallback to manual extraction if JSON parsing fails
                analysis = {
                    'skills': self.extract_skills(text),
                    'experience': self.extract_experience(text),
                    'education': self.extract_education(text)
                }

            # Enhance with NLP-based extraction
            analysis['skills'] = list(set(analysis.get('skills', []) + self.extract_skills(text)))
            
            return analysis

        except Exception as e:
            print(f"Error analyzing resume with Gemini: {e}")
            return None

    def extract_skills(self, text):
        """Extract skills using NLP."""
        tokens = word_tokenize(text.lower())
        # Remove stop words and punctuation
        words = [word for word in tokens if word.isalnum() and word not in self.stop_words]
        
        # Common technical and soft skills
        common_skills = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'aws',
            'leadership', 'communication', 'teamwork', 'problem-solving',
            'agile', 'scrum', 'project management', 'analytics', 'machine learning',
            'data science', 'cloud computing', 'devops', 'ci/cd'
        ]
        
        skills = [word for word in words if word in common_skills]
        return list(set(skills))

    def extract_experience(self, text):
        """Extract work experience using NLP."""
        experience = []
        lines = text.split('\n')
        
        current_exp = {}
        for line in lines:
            # Look for date patterns and job titles
            if any(year in line for year in [str(y) for y in range(1990, 2025)]):
                if current_exp:
                    experience.append(current_exp)
                current_exp = {'period': line}
            elif any(title in line.lower() for title in ['engineer', 'developer', 'manager', 'analyst', 'consultant']):
                if 'title' not in current_exp:
                    current_exp['title'] = line
            elif current_exp:
                if 'description' not in current_exp:
                    current_exp['description'] = line
                else:
                    current_exp['description'] += ' ' + line

        if current_exp:
            experience.append(current_exp)
            
        return experience

    def extract_education(self, text):
        """Extract education information using NLP."""
        education = []
        edu_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college']
        
        lines = text.split('\n')
        current_edu = {}
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in edu_keywords):
                if current_edu:
                    education.append(current_edu)
                current_edu = {
                    'degree': line,
                    'year': next((y for y in range(1990, 2025) if str(y) in line), None)
                }
            elif current_edu and 'institution' not in current_edu:
                current_edu['institution'] = line

        if current_edu:
            education.append(current_edu)
            
        return education

class JobMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def calculate_match_score_sync(self, candidate_data, job_requirements):
        """Calculate match score between candidate and job."""
        # Convert skills to text for vectorization
        candidate_skills = ' '.join(candidate_data['skills'])
        required_skills = ' '.join(job_requirements.get('skills', []))
        
        # Create TF-IDF vectors
        vectors = self.vectorizer.fit_transform([candidate_skills, required_skills])
        
        # Calculate cosine similarity
        similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        
        # Weight different factors
        skill_match = similarity * 0.5
        experience_match = self.calculate_experience_match(
            candidate_data['experience'],
            job_requirements.get('experience', {})
        ) * 0.3
        education_match = self.calculate_education_match(
            candidate_data['education'],
            job_requirements.get('education', {})
        ) * 0.2
        
        total_score = skill_match + experience_match + education_match
        
        # Get AI-powered analysis
        analysis = self.get_ai_analysis_sync(candidate_data, job_requirements)
        
        return {
            'total_score': total_score,
            'skill_match': skill_match,
            'experience_match': experience_match,
            'education_match': education_match,
            'ai_analysis': analysis
        }

    def calculate_experience_match(self, candidate_experience, required_experience):
        """Calculate experience match score."""
        if not candidate_experience or not required_experience:
            return 0.5
        
        # Calculate years of experience
        candidate_years = sum(len(exp.get('period', '').split('-')) for exp in candidate_experience)
        required_years = required_experience.get('minimum_years', 0)
        
        if candidate_years >= required_years:
            return 1.0
        elif candidate_years >= required_years * 0.7:
            return 0.8
        elif candidate_years >= required_years * 0.5:
            return 0.6
        else:
            return 0.4

    def calculate_education_match(self, candidate_education, required_education):
        """Calculate education match score."""
        if not candidate_education or not required_education:
            return 0.5
        
        education_levels = {
            'high school': 1,
            'associate': 2,
            'bachelor': 3,
            'master': 4,
            'phd': 5
        }
        
        candidate_level = max(
            education_levels.get(edu.get('degree', '').lower(), 0)
            for edu in candidate_education
        )
        required_level = education_levels.get(
            required_education.get('minimum_degree', '').lower(), 0
        )
        
        if candidate_level >= required_level:
            return 1.0
        elif candidate_level == required_level - 1:
            return 0.7
        else:
            return 0.4

    def get_ai_analysis_sync(self, candidate_data, job_requirements):
        """Get AI-powered analysis of the match."""
        try:
            prompt = f"""
            Analyze the match between this candidate and job requirements:

            Candidate Profile:
            - Skills: {', '.join(candidate_data['skills'])}
            - Experience: {json.dumps(candidate_data['experience'], indent=2)}
            - Education: {json.dumps(candidate_data['education'], indent=2)}

            Job Requirements:
            {json.dumps(job_requirements, indent=2)}

            Provide a detailed analysis in JSON format:
            {{
                "overall_assessment": "brief overall assessment",
                "strengths": ["list of key strengths"],
                "gaps": ["list of potential gaps"],
                "recommendations": ["specific recommendations for improvement"]
            }}
            """

            response = self.model.generate_content(prompt)
            
            try:
                analysis = json.loads(response.text)
            except json.JSONDecodeError:
                analysis = {
                    'overall_assessment': response.text,
                    'strengths': [],
                    'gaps': [],
                    'recommendations': []
                }
            
            return analysis

        except Exception as e:
            print(f"Error getting AI analysis: {e}")
            return {
                'overall_assessment': 'Analysis unavailable',
                'strengths': [],
                'gaps': [],
                'recommendations': []
            }