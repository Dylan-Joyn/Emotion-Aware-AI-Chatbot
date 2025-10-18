# Version 1.0.0

**Added**
<ul>
<li>CHANGELOG.md for version histroy</li>
<li>CI/CD Pipeline in workflows</li>
<li>Secrets have been uploaded to Github and established in workflow</li>

**Changed**
<ul>
<li>test_api actually utilizes pytests </li>

**Fixed**
<ul>
<li>test_api does not throw an error for import statements</li>

# Version 1.0.1

**Added**
<ul>
<li>Added a file named test_groq_api.py for testing GROQ</li>

**Changed**
<ul>
<li>Removed gemini_api_models_check.py as it is currently being done in test_api.py</li>
<li>test_api.py has been renamed to test_gemini_api.py

**Fixed**
<ul>
<li>Groq's API key and model it is currently running tests on in test_groq_api.py</li>
