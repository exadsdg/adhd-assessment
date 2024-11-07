import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import load_json_data, calculate_score, get_feedback, get_recommendation, get_category_description

# Page configuration
st.set_page_config(
    page_title="Avaliação TDAH - Ativa-Mente",
    page_icon="🧠",
    layout="centered"
)

# Cache data loading
@st.cache_data
def get_cached_data():
    return {
        'questions': load_json_data('data/questions.json')['questions'],
        'content': load_json_data('data/content.json')
    }

# Load cached data
cached_data = get_cached_data()
questions = cached_data['questions']
content = cached_data['content']

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

def validate_current_step():
    """Validate if the current step can be navigated away from."""
    if 1 <= st.session_state.step <= len(questions):
        current_question = questions[st.session_state.step - 1]
        return current_question['id'] in st.session_state.responses
    return True

def update_step(new_step):
    """Update step with minimal state changes."""
    if validate_current_step() and 0 <= new_step <= len(questions) + 2:
        if new_step != st.session_state.step:
            st.session_state.step = new_step
            st.session_state.current_response = None
            st.rerun()

def next_step():
    """Handle navigation to next step with validation."""
    if validate_current_step():
        update_step(st.session_state.step + 1)

def prev_step():
    """Handle navigation to previous step."""
    if st.session_state.step > 0:
        update_step(st.session_state.step - 1)

def handle_response(question_id: int, response: str):
    """Handle storing of responses without forcing rerun."""
    if response and (question_id not in st.session_state.responses or 
                    st.session_state.responses[question_id] != response):
        st.session_state.responses[question_id] = response
        st.session_state.current_response = response

def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='TDAH Indicators',
        line_color='#1B365D',
        fillcolor='rgba(27,54,93,0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(t=30, b=30)
    )
    return fig

def create_bar_chart(scores):
    df = pd.DataFrame({
        'Categoria': list(scores.keys()),
        'Pontuação': list(scores.values())
    })
    
    fig = px.bar(df, x='Categoria', y='Pontuação',
                 color='Pontuação',
                 color_continuous_scale=['#4CAF50', '#FFA500', '#FF6B6B'],
                 range_y=[0, 100])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(t=30, b=30)
    )
    return fig

# Pre-calculate progress
total_steps = len(questions) + 3  # +3 for intro, results, and CTA
progress = st.session_state.step / total_steps

# Create empty containers for dynamic content
header_container = st.empty()
content_container = st.empty()
feedback_container = st.empty()
navigation_container = st.empty()

# Main content
if st.session_state.step == 0:
    with st.container():
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.progress(progress)
        st.markdown(f"<h1 style='text-align: center; font-size: 24px; margin-top: 1rem;'>{content['intro']['title']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; margin: 1rem 0;'>{content['intro']['description']}</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="navigation-container">', unsafe_allow_html=True)
    if st.button("Começar Avaliação", use_container_width=True):
        next_step()
    st.markdown('</div>', unsafe_allow_html=True)

elif 1 <= st.session_state.step <= len(questions):
    question = questions[st.session_state.step - 1]
    
    with st.container():
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.progress(progress)
        st.markdown(f"<h2 style='text-align: center; font-size: 20px; margin-top: 1rem;'>Pergunta {st.session_state.step} de {len(questions)}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; margin: 1rem 0;'>{question['text']}</p>", unsafe_allow_html=True)
        
        current_value = st.session_state.responses.get(question['id'], None)
        response = st.radio(
            "Selecione uma opção",
            options=question['options'],
            key=f"q_{question['id']}",
            index=None if current_value is None else question['options'].index(current_value),
            label_visibility="collapsed"
        )
        
        if response is not None:
            handle_response(question['id'], response)
        
        if question['id'] in st.session_state.responses:
            feedback = get_feedback(question, st.session_state.responses[question['id']])
            st.markdown(f'<div class="feedback-box">{feedback}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="navigation-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Voltar", use_container_width=True, disabled=st.session_state.step == 1):
            prev_step()
    with col2:
        next_button_label = "Próximo →" if st.session_state.step < len(questions) else "Ver Resultados →"
        if st.button(next_button_label, use_container_width=True, disabled=not validate_current_step()):
            next_step()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == len(questions) + 1:
    scores = calculate_score(st.session_state.responses)
    
    with st.container():
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.progress(progress)
        st.markdown("<h1 style='text-align: center; font-size: 24px;'>Resultados da Avaliação</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; font-size: 20px; margin: 2rem 0;'>Análise por Área</h2>", unsafe_allow_html=True)
        
        # Radar Chart
        radar_fig = create_radar_chart(scores)
        st.plotly_chart(radar_fig, use_container_width=True)
        
        # Bar Chart
        bar_fig = create_bar_chart(scores)
        st.plotly_chart(bar_fig, use_container_width=True)
        
        # Detailed Analysis
        st.markdown("<h2 style='text-align: center; font-size: 20px; margin: 2rem 0;'>Análise Detalhada</h2>", unsafe_allow_html=True)
        for category, score in scores.items():
            severity = "Alta" if score >= 70 else "Moderada" if score >= 40 else "Baixa"
            color = "#FF6B6B" if score >= 70 else "#FFA500" if score >= 40 else "#4CAF50"
            
            st.markdown(f"""
            <div style="padding: 1.5rem; border-radius: 8px; background-color: #FFFFFF; margin: 1rem 0; border-left: 4px solid {color}">
                <h4 style="margin: 0 0 1rem 0;">{category.title()}</h4>
                <p style="margin: 0.5rem 0;">Intensidade: {severity} ({score:.1f}%)</p>
                <p style="margin: 0.5rem 0;">{get_category_description(category, severity)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        recommendation = get_recommendation(scores)
        st.info(recommendation)
        
        st.markdown("<h2 style='text-align: center; font-size: 20px; margin: 2rem 0;'>Como a Ativa-Mente pode ajudar:</h2>", unsafe_allow_html=True)
        cols = st.columns(len(content['platform_benefits']))
        for col, benefit in zip(cols, content['platform_benefits']):
            with col:
                st.markdown(f"""
                <div class="benefit-card">
                    <h3>{benefit['title']}</h3>
                    <p>{benefit['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="navigation-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Voltar ao Questionário", use_container_width=True):
            prev_step()
    with col2:
        if st.button("Ver Depoimentos →", use_container_width=True):
            next_step()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == len(questions) + 2:
    with st.container():
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.progress(progress)
        st.markdown("<h1 style='text-align: center; font-size: 24px;'>Depoimentos de Pais</h1>", unsafe_allow_html=True)
        
        for testimonial in content['testimonials']:
            st.markdown(f"""
            <div class="testimonial">
                <p style="margin: 1rem 0;">"{testimonial['text']}"</p>
                <p style="margin: 0.5rem 0;"><strong>{testimonial['name']}</strong></p>
                <p style="margin: 0;">{'⭐' * testimonial['rating']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; font-size: 20px; margin: 2rem 0;'>Comece sua jornada com a Ativa-Mente</h2>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="navigation-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Voltar para os Resultados", use_container_width=True):
            prev_step()
    with col2:
        if st.button("Experimente Gratuitamente →", use_container_width=True):
            st.success("Obrigado por seu interesse! Em breve você receberá um e-mail com as instruções de acesso.")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("<p style='text-align: center; padding: 2rem 0;'>Desenvolvido com ❤️ pela Ativa-Mente</p>", unsafe_allow_html=True)