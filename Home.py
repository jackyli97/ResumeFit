import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

import json
from io import StringIO
import pdfplumber
import docx
import base64

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def read_resume(file):
    if file.type == "text/plain":
        # Read text file
        text = str(file.read(), "utf-8")
    elif file.type == "application/pdf":
        # Extract text from PDF
        with pdfplumber.open(file) as pdf:
            text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Extract text from DOCX
        doc = docx.Document(file)
        text = '\n'.join(paragraph.text for paragraph in doc.paragraphs if paragraph.text)
    else:
        text = "Unsupported file type"
    return text

def compare_resume_to_job_description(resume_file, job_description_text):
  if not api_key:
        st.error("OpenAI API key is not set. Please set it in your environment variables.")
        return
  
  model = "gpt-4-turbo"

  if not resume_file:
    st.error("Resume file could not be read.")
    return

  resume_text = read_resume(resume_file)
  prompt = f"""
    Firstly, instantiate an empty dictionary, this will be used to return JSON object with 6 key-value pairs as the message response to this prompt

    You have 6 individual tasks, each correalating to an entry in our output dictionary. Each of the tasks will require you\n
    to read from two data sources, which will be referred to as 'job_description_text' and 'resume_text' respectively. 
    
    This right here is the job description, so please refer back this when you need to look up anything in job_description_text:
    '''{job_description_text}'''

    And now this right here is the resume to analyze, so please refer back this when you need to look up anything in resume_text:
    ```{resume_text}```

    1) Inspect job_description_text, and determine what the education requirements are for the job. Then inspect resume_text to determine if the education requirements from the \n
    job description are found and met in the resume. Assign a new key-value pair to the python dictionary, with the key named 'education_requirements_met', and the value being the\n
    a boolean representing whether or not the education requirements were met based on the resume.

    2) Inspect job_description_text, and determine what the years of experience required are for the job. Then inspect resume_text to determine if the years of experience from the \n
    job description are found and met in the resume. Assign a new key-value pair to the python dictionary, with the key named 'years_of_experience_met', and the value being the\n
    a boolean representing whether or not the experience requirements were met based on the resume.

    3) Inspect job_description_text, which can be found slightly earlier in this prompt message, as the body of text that is delimited and wrapped by triple single quotes\n
    and identify 10 keywords found in the description that represent desired skills, tools, and qualities that the job posters are looking for.\n
    Example keywords are: Python, Javascript, Artificial Intelligence, automation tools, C++, Git, Linux, version control, web services, etc.. \n
    If you cannot find 10 good keywords, do not force it, just add however much you can then in those cases.\n
    Assign a new key-value pair to the dictionary, with the key named 'keywords_from_job_description', and the value being the\n
    the list of keywords collected here in this task.

    4) Firstly instantiate an empty list\n
    Given the list that is the value of job_description_text in the dictionary, Iterate through the list using a for loop, and for each element, I want you to\n
    search resume_text, which can be found slightly earlier in this prompt message, as the body of text that is delimited and wrapped by triple back ticks\n
    for exact matches of the keyword, case insensitive matches are okay. Do this by performing a regex search with the resume_text as the input, and \n
    the current keyword as the target, the regex experession should be case-insenstive. Please use re.match, instead of re.search for accuracy. So inside of the for loop\n
    You should be calling something like this, 're.match(resume_text, currKeyword)', if the regex exp returns None, then append a value of 0 to the list created \n
    Else, push a value of 1, indicating we found a match. Assign a new key-value pair to the python dictionary, with the key named 'keywords_matches', and the value should be the created list,\n
    which should now be full of 0s or 1s, and be the same length as the list that is the value of job_description_text in the dictionary\n
  
    5) Based on the findings above: the number of keywords from the job description that the resume contains, and whether or not the job seeker fulfils the education and years of experience\n
    requirements, calculate a qualifcation percentage. Assign a new key-value pair to the python dictionary, with the key named 'qualification_percentage', and the value being the\n
    a number representing the qualification percentage.

    6) Write feedback for the job seeker. Include positive feedback on what makes them a good fit for the role and what their resume does a good job of,\n
    and also discuss skill gaps, and any helpful resume advice and tips. And lastly throw in a quick word of encouragement. \n
    Assign a new key-value pair to the python dictionary, with the key named 'feedback', and the value being the\n
    a string reprenting the feedback you just wrote.

    Your dictionary that you created, and that was initially empty, but should be filled out now after the above tasks, is now ready to be returned as the message. Ensure that what\n
    you are returning is of a JSON type, and not wrapped in quotes.

    ''
    {{
      education_requirements_met: boolean,
      years_of_experience_met: boolean,
      keywords_from_job_description: string[],
      keywords_matches: number[],
      qualification_percentage: number,
      feedback: string
    }}
    ''
  """

  messages = [
      {"role": "system", "content": "You are an expert career coach who helps analayzes a candiate's fit for role given a resume and a job description."},
      {"role": "user", "content": prompt}
  ]
  response = client.chat.completions.create(
      model=model,
      response_format={ "type": "json_object" },
      messages=messages,
      temperature=0
  )

  return json.loads(response.choices[0].message.content)

def plot_heatmap_of_keywords_matches(keywords,matches):
    data = {
        "keywords": keywords,
        "matches": matches
    }

    # Create DataFrame
    df_keywords_matches = pd.DataFrame(data)

    # Create a color map
    cmap = sns.color_palette("coolwarm", as_cmap=True)

    # Mapping 1 to green and 0 to red
    lut = {1: 'green', 0: 'red'}
    row_colors = df_keywords_matches["matches"].map(lut)

    # Plotting
    fig, ax = plt.subplots()
    plt.figure(figsize=(12, 4))
    g = sns.heatmap(df_keywords_matches[["matches"]].T, cmap=cmap, annot=True, cbar=False, yticklabels=[], xticklabels=df_keywords_matches["keywords"], linewidths=.5, ax=ax)
    g.set_title('Heatmap of Keyword Matches Found in Resume', weight="bold", fontsize=14)
    g.set_ylabel("Found in Resume (1 for Yes, 0 for No)", weight="bold")
    g.set_xlabel("Keywords", weight="bold")
    g.set_xticklabels(df_keywords_matches["keywords"], rotation=45, ha="right") 
    st.pyplot(fig)

def display_json_response(resume_analysis):
    st.header("Your Tailored ResumeFit Report")
    st.subheader("Qualification Percentage")
    st.markdown(f'{resume_analysis["qualification_percentage"]}%')

    st.subheader("Education Requirement Met")
    if resume_analysis["education_requirements_met"] == True:
        st.markdown("Yes")
    else:
        st.markdown("No")

    st.subheader("Years of Experience Met")
    if resume_analysis["years_of_experience_met"] == True:
        st.markdown("Yes")
    else:
        st.markdown("No")

    st.subheader("Keywords From Job Description")
    st.markdown(', '.join(resume_analysis["keywords_from_job_description"]))

    keywords_matches = []
    for idx, bool_val in enumerate(resume_analysis["keywords_matches"]):
        if bool_val == 1:
            keywords_matches.append(resume_analysis["keywords_from_job_description"][idx])
    st.subheader(f'{len(keywords_matches)} Matching Keywords Found In Your Resume')
    st.markdown(', '.join(keywords_matches))

    st.subheader("Summary")
    st.markdown(resume_analysis["feedback"])

st.title(':blue[ResumeFit]')
st.header("Streamlining job applications with AI", divider='rainbow')
st.markdown('Analyze and compare resumes with job postings to identify skill gaps and areas for improvement.')


st.subheader("Get Started", divider='blue')
st.markdown('Upload your resume via various supported formats, and then paste job description. Now sit back as AI does the rest of the work.')
st.page_link("pages/Get_Job_Description_From_URL.py", label="Click here to let us do the work and generate the job description from a job link", icon="🤖")
with st.form("resume_and_job_info_form"):
    resume_col, job_description_col = st.columns(2)
    with resume_col:
        resume_file = st.file_uploader("Upload your resume:", type=['txt', 'pdf', 'docx'])
        # Add help text or caption below the uploader
        st.caption("Supported formats: .txt, .pdf, .docx")
    with job_description_col:
        job_description_text = st.text_area("Paste the job description here:", height=300)
    submit = st.form_submit_button('Analyze Your Fit')

if submit:
    if not resume_file or job_description_text == "":
        st.error("Cannot start analysis until both resume and job description have been uploaded")
    else:
        with st.spinner('In the lab analyzing your resume and the job listing...'):
            resume_analysis = compare_resume_to_job_description(resume_file, job_description_text)
            display_json_response(resume_analysis)
            plot_heatmap_of_keywords_matches(resume_analysis["keywords_from_job_description"], resume_analysis["keywords_matches"])
        

