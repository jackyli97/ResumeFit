import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def get_job_description_from_url(url, source):
    if not api_key:
        st.error("OpenAI API key is not set. Please set it in your environment variables.")
        return
  
    model = "gpt-3.5-turbo"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises a HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        if source == "Linkedin":
            job_details_html = soup.find('div', class_="description__text description__text--rich")
        elif source == "Greenhouse":
            job_details_html = soup.find('div', id="content")
        elif source == "SmartRecruiters":
            job_details_html = soup.find('main', class_="jobad-main job")

        if job_details_html is None:
            return """
                The job description could not be generated. Please try again and ensure you are selecting the correct job site source and that you are using the
                direct link to the job and not just on a page with a list of jobs or something similar. If issue continues to arise, you have to manually copy and paste the job description
                directly from the site.
            """
    
        prompt = f"""
        Given this HTML from a job page, can you please return to me the extracted job description in regular text format.

        {job_details_html}
        """

        messages = [
            {"role": "system", "content": "You are an advanced ai model capable of processing large html code and extracting desired information from it and returning it."},
            {"role": "user", "content": prompt}
        ]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0
        )

        return response.choices[0].message.content
    except requests.RequestException as e:
        return f"Error fetching job description: {str(e)}"
    
st.title(':blue[ResumeFit]')
st.header("Get Job Description From URL", divider='rainbow')
st.markdown('Paste the link to the job you are interested in, and let us grab the job description for you, so you can paste into our ResumeFit analyzer on the home page')

with st.form("job_description_form"):
    job_description_url = st.text_input("Paste the job description URL here:")
    job_site = st.radio("Choose which site the job listing is from:", ('Linkedin', 'Greenhouse', 'SmartRecruiters'))
    st.caption("If the job is not from one of our supported sites, you will have to just copy and paste the job description manually. Reach out to us and we can look to add support in our future roadmap :)")

    submit = st.form_submit_button('Generate Job Description')

if submit:
    if not job_description_url:
        st.error("Please paste the url for a job to proceed.")
    else:
        with st.spinner('Generating your job description...'):
            job_description_text = get_job_description_from_url(job_description_url, job_site)
            st.text_area("Generated Job Description", job_description_text, height=300)

st.markdown('##')
st.page_link("Home.py", label="Click here to return home and paste your generated job description into the analyzer", icon="🏠")
