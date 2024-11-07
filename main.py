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
if 'current_response' not in st.session_state:
    st.session_state.current_response = None

def next_step():
    # Validate current response before proceeding
    if 1 <= st.session_state.step <= len(questions):
        current_question = questions[st.session_state.step - 1]
        if current_question['id'] not in st.session_state.responses:
            st.error("Por favor, responda a pergunta antes de continuar.")
            return
    st.session_state.step += 1
    # Reset current response when moving to next question
    st.session_state.current_response = None

def prev_step():
    st.session_state.step -= 1
    # Reset current response when moving to previous question
    st.session_state.current_response = None

def handle_response(question_id: int, response: str):
    st.session_state.responses[question_id] = response
    st.session_state.current_response = response

# Progress bar with smoother transition
progress = st.session_state.step / (len(questions) + 3)  # +3 for intro, results, and CTA
st.progress(progress)

# Main content
if st.session_state.step == 0:
    # Introduction
    st.title(content['intro']['title'])
    st.write(content['intro']['description'])
    
    # Add container for better button placement
    with st.container():
        st.button("Começar Avaliação", on_click=next_step, use_container_width=True)

elif 1 <= st.session_state.step <= len(questions):
    # Questions
    question = questions[st.session_state.step - 1]
    
    # Question container for better spacing
    with st.container():
        st.subheader(f"Pergunta {st.session_state.step} de {len(questions)}")
        
        # Get previous response if it exists
        default_index = (
            question['options'].index(st.session_state.responses[question['id']])
            if question['id'] in st.session_state.responses
            else 0
        )
        
        response = st.radio(
            question['text'],
            options=question['options'],
            key=f"q_{question['id']}",
            index=default_index
        )
        
        # Store response immediately when selected
        if response != st.session_state.current_response:
            handle_response(question['id'], response)
        
        # Show feedback if question was answered
        if question['id'] in st.session_state.responses:
            feedback = get_feedback(question, st.session_state.responses[question['id']])
            st.markdown(f'<div class="feedback-box">{feedback}</div>', unsafe_allow_html=True)
    
    # Navigation container for better button layout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Voltar", use_container_width=True):
            prev_step()
    with col2:
        if st.button("Próximo →", use_container_width=True):
            next_step()

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
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Voltar para o Questionário", use_container_width=True):
            prev_step()
    with col2:
        if st.button("Ver Depoimentos →", use_container_width=True):
            next_step()

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
    
    # Navigation and CTA buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Voltar para os Resultados", use_container_width=True):
            prev_step()
    with col2:
        if st.button("Experimente Gratuitamente →", use_container_width=True):
            st.success("Obrigado por seu interesse! Em breve você receberá um e-mail com as instruções de acesso.")

# Footer
st.markdown("---")
st.markdown("Desenvolvido com ❤️ pela Ativa-Mente | Este questionário não substitui uma avaliação profissional")
