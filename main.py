import streamlit as st
import pandas as pd
from utils import load_json_data, calculate_score, get_feedback, get_recommendation

# Page configuration
st.set_page_config(
    page_title="Avaliação TDAH - Ativa-Mente",
    page_icon="🧠",
    layout="centered"
)

# Load data
questions = load_json_data('data/questions.json')['questions']
content = load_json_data('data/content.json')

# Load custom CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'responses' not in st.session_state:
    st.session_state.responses = {}

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

# Progress bar
progress = st.session_state.step / (len(questions) + 3)  # +3 for intro, results, and CTA
st.progress(progress)

# Main content
if st.session_state.step == 0:
    # Introduction
    st.title(content['intro']['title'])
    st.write(content['intro']['description'])
    st.button("Começar Avaliação", on_click=next_step)

elif 1 <= st.session_state.step <= len(questions):
    # Questions
    question = questions[st.session_state.step - 1]
    st.subheader(f"Pergunta {st.session_state.step} de {len(questions)}")
    
    response = st.radio(
        question['text'],
        options=question['options'],
        key=f"q_{question['id']}"
    )
    
    if st.button("Próximo"):
        st.session_state.responses[question['id']] = response
        next_step()
    
    if st.button("Voltar"):
        prev_step()
    
    # Show feedback if question was already answered
    if question['id'] in st.session_state.responses:
        feedback = get_feedback(question, st.session_state.responses[question['id']])
        st.markdown(f'<div class="feedback-box">{feedback}</div>', unsafe_allow_html=True)

elif st.session_state.step == len(questions) + 1:
    # Results page
    st.title("Resultados da Avaliação")
    
    scores = calculate_score(st.session_state.responses)
    
    # Display scores
    st.subheader("Análise por Área")
    for category, score in scores.items():
        st.write(f"{category.title()}: {score:.1f}%")
        st.progress(score/100)
    
    # Show recommendation
    recommendation = get_recommendation(scores)
    st.info(recommendation)
    
    # Platform benefits
    st.subheader("Como a Ativa-Mente pode ajudar:")
    cols = st.columns(len(content['platform_benefits']))
    for col, benefit in zip(cols, content['platform_benefits']):
        with col:
            st.markdown(f"""
            <div class="benefit-card">
                <h3>{benefit['title']}</h3>
                <p>{benefit['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.button("Ver Depoimentos", on_click=next_step)
    
elif st.session_state.step == len(questions) + 2:
    # Testimonials
    st.title("Depoimentos de Pais")
    
    for testimonial in content['testimonials']:
        st.markdown(f"""
        <div class="testimonial">
            <p>"{testimonial['text']}"</p>
            <p><strong>{testimonial['name']}</strong></p>
            {'⭐' * testimonial['rating']}
        </div>
        """, unsafe_allow_html=True)
    
    # Call to Action
    st.subheader("Comece sua jornada com a Ativa-Mente")
    if st.button("Experimente Gratuitamente"):
        st.success("Obrigado por seu interesse! Em breve você receberá um e-mail com as instruções de acesso.")
    
    if st.button("Voltar para os Resultados"):
        prev_step()

# Footer
st.markdown("---")
st.markdown("Desenvolvido com ❤️ pela Ativa-Mente | Este questionário não substitui uma avaliação profissional")
