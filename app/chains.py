import os
from dotenv import load_dotenv
import streamlit as st 
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
import re
# Charger les variables d'environnement
load_dotenv()

# Centralisation des prompts
PROMPTS = {
    "French": """
    ### DESCRIPTION DU POSTE:
    {job_description}

    ### INSTRUCTION:
    En vous basant sur la description du poste ci-dessus, rédigez un email professionnel en français pour postuler à ce poste. L'email doit mettre en avant vos compétences, votre intérêt pour le rôle,  et comment vous répondez aux exigences du poste en débutant par me présenter comme {mentions}  qui sont des details comme nom et prénom et d'autre details. Le ton doit être formel mais enthousiaste.
    """,
    "German": """
    ### JOBBESCHREIBUNG:
    {job_description}

    ### ANWEISUNG:
    Basierend auf der obigen Stellenbeschreibung verfassen Sie eine professionelle E-Mail auf Deutsch, in der Sie sich auf die Position bewerben. Betonen Sie Ihre Fähigkeiten, Ihr Interesse an der Rolle und wie Sie die Anforderungen erfüllen und beginnen Sie damit, mich als {mentions} vorzustellen.. Die E-Mail sollte formal und motiviert klingen.
    """,
    "English": """
    ### JOB DESCRIPTION:
    {job_description}

    ### INSTRUCTION:
    Based on the job description above, draft a professional email in English to apply for the position. Highlight your skills, your interest in the role, and how you meet the job requirements and begin by presenting me that {mentions}. The email should be formal but also convey enthusiasm and commitment to the opportunity.
    """
}

# Fonction pour récupérer le prompt adapté à la langue
def get_prompt_template(selected_language):
    return PROMPTS.get(selected_language, PROMPTS["English"])



class Chain:
    def __init__(self):
        # Initialisation du LLM
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-70b-versatile"
        )
    

    def extract_jobs(self, cleaned_text):
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the following keys: `role`, `experience`, `skills` , `description`and `mentions`.
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]
      
    def write_mail(self, job, links, language,mentions) :
        """Generates an email for the job application in the selected language and mention the name and university and all details mentionnedof the sender in section mentions."""
        # Get the email prompt template for the selected language
        prompt_template = get_prompt_template(language)

        # Create the email writing chain
        prompt_email = PromptTemplate.from_template(prompt_template)
        chain_email = prompt_email | self.llm

        # Debugging: Log the job data
        print("DEBUG: Job data passed to write_mail:", job)

        # Ensure all job fields have valid data
        job_description = job.get('description', 'No description provided.')
        skills = job.get('skills', [])
        if not isinstance(skills, list):  # Ensure 'skills' is a list
            st.error(f"'skills' field is not a list. Value: {skills}")
            skills = []

        role = job.get('role', 'No role specified')

        # Debugging: Log the processed data
        print("DEBUG: Processed data:")
        print(f" - Description: {job_description}")
        print(f" - Skills: {skills}")
        print(f" - Role: {role}")
        print(f" - Links: {links}")
        print(f" - Mentions: {mentions}")

        try:
            # Invoke the chain with the job data
            res = chain_email.invoke({
                "job_description": job_description,
                "mentions":mentions,
                "skills": ', '.join(skills),  # Safely join skills
                "role": role,
                "link_list": links or [] , # Default to an empty list if links is None
                
            })

            # Return the generated email content
            return res.content

        except Exception as e:
            st.error(f"Failed to generate email: {str(e)}")
            return "An error occurred while generating the email."

        



   


if __name__ == "__main__":
    # Exemple : Chargement de la clé d'API pour vérifier si elle est bien récupérée
    print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))