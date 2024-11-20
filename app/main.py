import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from utils import clean_text


def create_streamlit_app(chain, portfolio, clean_text):
    # Choix de la langue pour générer l'email
    language_options = ['English', 'French', 'German']  # Ajoutez d'autres langues si nécessaire
    selected_language = st.selectbox("Select Language:", language_options)
    
    st.title("📧 Mail Generator")
    
    # Entrée de l'URL
    url_input = st.text_input("Enter a URL:", value="")
    
    # Mention d'informations personnelles et d'intérêt
    mentions = st.text_area(
        "What do you want to mention (Personal information and your interest):",
        placeholder="I am X, currently studying in Y university, and I am interested in..."
    )
    
    # Bouton pour soumettre
    submit_button = st.button("Submit")

    if submit_button:
        if url_input:  # Vérifier si l'URL est fournie
            try:
                # Charger le contenu de la page Web
                loader = WebBaseLoader([url_input])
                raw_data = loader.load()
                
                if not raw_data:
                    st.error("Failed to retrieve data from the URL.")
                    return
                
                # Nettoyer les données extraites
                data = clean_text(raw_data.pop().page_content)
                
                # Charger le portfolio
                portfolio.load_portfolio()
                
                # Extraction des offres d'emploi
                jobs = chain.extract_jobs(data)
                
                if not jobs:
                    st.warning("No jobs found in the provided URL.")
                    return
                
                # Génération d'e-mails pour chaque emploi
                for job in (jobs):
                    skills = job.get('skills', [])
                    links = portfolio.query_links(skills)
                    email = chain.write_mail(job, links, selected_language, mentions )
                    st.code(email, language='markdown')
                    
                                
            except Exception as e:
                st.error(f"An Error Occurred: {e}")
        else:
            st.warning("Please provide a valid URL.")


if __name__ == "__main__":
    # Initialisation des objets nécessaires
    chain = Chain()
    portfolio = Portfolio()
    
    # Configuration de la page Streamlit
    st.set_page_config(layout="wide", page_title="Email Generator", page_icon="📧")
    
    # Lancement de l'application Streamlit
    create_streamlit_app(chain, portfolio, clean_text)