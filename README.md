# AI-Powered Resume Screening System

A modern web application that leverages AI to automate and enhance the resume screening process. Built with Flask, Tailwind CSS, and modern frontend technologies.

## Features

- Modern, responsive UI built with Tailwind CSS
- AI-powered resume analysis
- Candidate-job matching
- Analytics and reporting dashboard
- Interactive data visualizations
- Real-time resume upload and processing

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-resume-screening
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

## Project Structure

```
ai-resume-screening/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
└── templates/             # HTML templates
    ├── base.html          # Base template with common elements
    ├── index.html         # Landing page
    ├── login.html         # Login page
    ├── dashboard.html     # Main dashboard
    ├── upload.html        # Resume upload page
    ├── jobs.html          # Job listings page
    └── report.html        # Analytics and reports page
```

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: 
  - Tailwind CSS for styling
  - Chart.js for data visualization
  - Font Awesome for icons
  - Google Fonts for typography
- **JavaScript Libraries**:
  - Chart.js for interactive charts
  - Core JavaScript for UI interactions

## Features in Detail

### 1. Resume Upload and Analysis
- Drag-and-drop interface for resume uploads
- Support for multiple file formats (PDF, DOC, DOCX)
- AI-powered extraction of key information:
  - Skills and technologies
  - Work experience
  - Education
  - Projects and achievements

### 2. Job Posting Management
- Create and manage job postings
- Define required skills and qualifications
- Set experience levels and job locations
- Track application status

### 3. Intelligent Matching
- AI-driven matching between resumes and job postings
- Scoring based on skills alignment
- Experience level matching
- Education requirements verification

### 4. Analytics Dashboard
- Real-time recruitment pipeline metrics
- Skills distribution analysis
- Department-wise hiring trends
- Time-to-hire tracking
- Interactive charts and visualizations

### 5. User Interface
- Clean, modern design with Tailwind CSS
- Responsive layout for all devices
- Intuitive navigation
- Real-time feedback and notifications

## Security Features

- Secure file upload handling
- Input validation and sanitization
- Protected routes and authentication
- Secure storage of sensitive information

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Tailwind CSS for the modern UI framework
- Font Awesome for the comprehensive icon set
- Chart.js for powerful data visualization
- The Flask community for the excellent web framework# jobu
