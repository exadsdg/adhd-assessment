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

# Display logo
st.image("DALL·E 2024-11-05 14.57.07 - Design a logo for a children's platform called 'Ativa-Mente', focused on enhancing focus and attention in young people with ADHD. The logo should be b.webp", 
        use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing

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
            st.experimental_rerun()

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
        height=400
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
        height=300
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

# Progress bar
st.progress(progress)

# Main content
if st.session_state.step == 0:
    with header_container:
        st.title(content['intro']['title'])
        st.write(content['intro']['description'])
    
    with content_container:
        if st.button("Começar Avaliação", use_container_width=True):
            next_step()

elif 1 <= st.session_state.step <= len(questions):
    question = questions[st.session_state.step - 1]
    
    with header_container:
        st.subheader(f"Pergunta {st.session_state.step} de {len(questions)}")
    
    with content_container:
        current_value = st.session_state.responses.get(question['id'], None)
        response = st.radio(
            question['text'],
            options=question['options'],
            key=f"q_{question['id']}",
            index=None if current_value is None else question['options'].index(current_value)
        )
        
        if response is not None:
            handle_response(question['id'], response)
    
    with feedback_container:
        if question['id'] in st.session_state.responses:
            feedback = get_feedback(question, st.session_state.responses[question['id']])
            st.markdown(f'<div class="feedback-box">{feedback}</div>', unsafe_allow_html=True)
    
    with navigation_container:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Voltar", use_container_width=True, disabled=st.session_state.step == 1):
                prev_step()
        with col2:
            next_button_label = "Próximo →" if st.session_state.step < len(questions) else "Ver Resultados →"
            if st.button(next_button_label, use_container_width=True, disabled=not validate_current_step()):
                next_step()

elif st.session_state.step == len(questions) + 1:
    # Cache scores calculation
    @st.cache_data
    def get_cached_scores(responses_key):
        return calculate_score(st.session_state.responses)
    
    scores = get_cached_scores(str(st.session_state.responses))
    
    with header_container:
        st.title("Resultados da Avaliação")
    
    with content_container:
        st.subheader("Análise por Área")
        
        # Radar Chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        radar_fig = create_radar_chart(scores)
        st.plotly_chart(radar_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Bar Chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        bar_fig = create_bar_chart(scores)
        st.plotly_chart(bar_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Detailed Analysis
        st.subheader("Análise Detalhada")
        for category, score in scores.items():
            severity = "Alta" if score >= 70 else "Moderada" if score >= 40 else "Baixa"
            color = "#FF6B6B" if score >= 70 else "#FFA500" if score >= 40 else "#4CAF50"
            
            st.markdown(f"""
            <div style="padding: 15px; border-radius: 5px; background-color: #FFFFFF; margin: 10px 0; border-left: 4px solid {color}">
                <h4>{category.title()}</h4>
                <p>Intensidade: {severity} ({score:.1f}%)</p>
                <p>{get_category_description(category, severity)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        recommendation = get_recommendation(scores)
        st.info(recommendation)
        
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

    with navigation_container:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Voltar ao Questionário", use_container_width=True):
                prev_step()
        with col2:
            if st.button("Ver Depoimentos →", use_container_width=True):
                next_step()

elif st.session_state.step == len(questions) + 2:
    with header_container:
        st.title("Depoimentos de Pais")
    
    with content_container:
        for testimonial in content['testimonials']:
            st.markdown(f"""
            <div class="testimonial">
                <p>"{testimonial['text']}"</p>
                <p><strong>{testimonial['name']}</strong></p>
                {'⭐' * testimonial['rating']}
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("Comece sua jornada com a Ativa-Mente")
    
    with navigation_container:
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
