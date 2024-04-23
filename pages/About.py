import streamlit as st

image = open("assets/jacky.png", "rb").read()

st.title("About")
st.markdown("Hi, I'm Jacky, the creator of this ResumeFit app. I am a software engineer diving into the world of AI development and data.\n\n Thank you taking the time to check it and hope you enjoy it and find it useful. If you would like to connect, my Linkedin and Github can be found below.")
st.image(image)

st.link_button(label="Linkedin", url="https://www.linkedin.com/in/jackyxli/")
st.link_button(label="Github", url="https://github.com/jackyli97/")