import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import load_json_data, calculate_score, get_feedback, get_recommendation, get_category_description, get_category_recommendations

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

# Initialize session state with improved validation
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'validation_message' not in st.session_state:
    st.session_state.validation_message = None
if 'transition_state' not in st.session_state:
    st.session_state.transition_state = 'ready'

def validate_current_step():
    """Enhanced validation with specific feedback."""
    if 1 <= st.session_state.step <= len(questions):
        current_question = questions[st.session_state.step - 1]
        is_valid = current_question['id'] in st.session_state.responses
        if not is_valid:
            st.session_state.validation_message = "Por favor, selecione uma resposta antes de continuar."
        else:
            st.session_state.validation_message = None
        return is_valid
    return True

def update_step(new_step):
    """Smooth step transition with validation."""
    if validate_current_step() and 0 <= new_step <= len(questions) + 2:
        st.session_state.transition_state = 'transitioning'
        st.session_state.step = new_step
        st.session_state.validation_message = None
        st.rerun()

def next_step():
    """Enhanced navigation to next step."""
    if validate_current_step():
        update_step(st.session_state.step + 1)

def prev_step():
    """Enhanced navigation to previous step."""
    if st.session_state.step > 0:
        update_step(st.session_state.step - 1)

def handle_response(question_id: int, response: str):
    """Enhanced response handling with validation."""
    if response and (question_id not in st.session_state.responses or 
                    st.session_state.responses[question_id] != response):
        st.session_state.responses[question_id] = response
        st.session_state.validation_message = None

def create_radar_chart(scores):
    """Enhanced radar chart with clinical thresholds."""
    categories = list(scores.keys())
    values = list(scores.values())
    
    fig = go.Figure()
    
    # Add clinical thresholds
    fig.add_trace(go.Scatterpolar(
        r=[70] * len(categories),
        theta=categories,
        fill=None,
        name='Limiar Clínico',
        line=dict(color='rgba(255,0,0,0.5)', dash='dash')
    ))
    
    # Add moderate threshold
    fig.add_trace(go.Scatterpolar(
        r=[40] * len(categories),
        theta=categories,
        fill=None,
        name='Limiar Moderado',
        line=dict(color='rgba(255,165,0,0.5)', dash='dash')
    ))
    
    # Add scores
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Perfil TDAH',
        line_color='#1B365D',
        fillcolor='rgba(27,54,93,0.3)',
        hovertemplate='%{theta}: %{r:.1f}%<br>Severidade: %{customdata}<extra></extra>',
        customdata=[get_severity_level(v) for v in values]
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[0, 20, 40, 60, 70, 80, 100],
                ticktext=['0%', '20%', '40%', '60%', '70%', '80%', '100%']
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(t=30, b=30)
    )
    return fig

def create_bar_chart(scores):
    """Enhanced bar chart with clinical context."""
    df = pd.DataFrame({
        'Categoria': list(scores.keys()),
        'Pontuação': list(scores.values()),
        'Severidade': [get_severity_level(score) for score in scores.values()]
    })
    
    fig = px.bar(df, x='Categoria', y='Pontuação',
                 color='Pontuação',
                 color_continuous_scale=[
                     [0, '#4CAF50'],    # Verde para baixo
                     [0.4, '#FFA500'],  # Laranja para moderado
                     [0.7, '#FF6B6B'],  # Vermelho para alto
                     [1, '#FF0000']     # Vermelho escuro para muito alto
                 ],
                 range_y=[0, 100])
    
    # Add threshold lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", 
                 annotation_text="Limiar Clínico (70%)")
    fig.add_hline(y=40, line_dash="dash", line_color="orange",
                 annotation_text="Limiar Moderado (40%)")
    
    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>' +
                      'Pontuação: %{y:.1f}%<br>' +
                      'Severidade: %{customdata}<extra></extra>',
        customdata=df['Severidade']
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(t=30, b=30)
    )
    return fig

def get_severity_level(score):
    """Get clinical severity level."""
    if score >= 80:
        return "Muito Alto"
    elif score >= 70:
        return "Alto"
    elif score >= 40:
        return "Moderado"
    return "Baixo"

# Pre-calculate progress
total_steps = len(questions) + 3  # +3 for intro, results, and CTA
progress = st.session_state.step / total_steps

# Main content
if st.session_state.step == 0:
    with st.container():
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.progress(progress)
        st.markdown(f"<h1 style='text-align: center; font-size: 24px;'>{content['intro']['title']}</h1>", unsafe_allow_html=True)
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
        st.markdown(f"<h2 style='text-align: center; font-size: 20px;'>Pergunta {st.session_state.step} de {len(questions)}</h2>", unsafe_allow_html=True)
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
            
        if st.session_state.validation_message:
            st.warning(st.session_state.validation_message)
        
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
        
        # Clinical Overview with Severity Indicators
        avg_score = sum(scores.values()) / len(scores)
        severity_level = get_severity_level(avg_score)
        severity_color = "#FF0000" if avg_score >= 80 else "#FF6B6B" if avg_score >= 70 else "#FFA500" if avg_score >= 40 else "#4CAF50"
        
        st.markdown(f"""
        <div style="text-align: center; margin: 1rem 0;">
            <h2 style="font-size: 20px;">Nível de Severidade Global</h2>
            <div style="background-color: {severity_color}; color: white; padding: 1rem; border-radius: 8px; display: inline-block;">
                <span style="font-size: 24px; font-weight: bold;">{severity_level}</span>
                <br>
                <span>Score Global: {avg_score:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced Visualization Section
        st.markdown("<h2 style='text-align: center; font-size: 20px;'>Análise Comparativa</h2>", unsafe_allow_html=True)
        
        # Radar Chart with clinical thresholds
        radar_fig = create_radar_chart(scores)
        st.plotly_chart(radar_fig, use_container_width=True)
        
        # Bar Chart with severity levels
        bar_fig = create_bar_chart(scores)
        st.plotly_chart(bar_fig, use_container_width=True)
        
        # Clinical Insights
        st.markdown("<h2 style='text-align: center; font-size: 20px;'>Análise Clínica Detalhada</h2>", unsafe_allow_html=True)
        
        # Add percentile information
        percentiles = {
            'concentracao': min(round(scores['concentracao'] / 0.8), 99),
            'impulsividade': min(round(scores['impulsividade'] / 0.8), 99),
            'hiperatividade': min(round(scores['hiperatividade'] / 0.8), 99)
        }
        
        for category, score in scores.items():
            severity = get_severity_level(score)
            color = "#FF0000" if score >= 80 else "#FF6B6B" if score >= 70 else "#FFA500" if score >= 40 else "#4CAF50"
            
            st.markdown(f"""
            <div style="padding: 1.5rem; border-radius: 8px; background-color: #FFFFFF; margin: 1rem 0; border-left: 4px solid {color}">
                <h4 style="margin: 0 0 1rem 0;">{category.title()}</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <div>
                        <strong>Nível de Severidade:</strong> {severity} ({score:.1f}%)
                        <br>
                        <strong>Percentil:</strong> {percentiles[category]}
                    </div>
                    <div style="text-align: right;">
                        <span style="background-color: {color}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px;">
                            {severity}
                        </span>
                    </div>
                </div>
                <div style="margin: 1rem 0;">
                    <strong>Padrões Comportamentais:</strong>
                    <p style="margin: 0.5rem 0;">{get_category_description(category, severity)}</p>
                </div>
                <div style="margin-top: 1rem;">
                    <strong>Recomendações da Ativa-Mente:</strong>
                    <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                        {get_category_recommendations(category, severity)}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Social Proof Section
        st.markdown("""
            <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 8px; margin: 2rem 0;">
                <h2 style="text-align: center; color: #1B365D; margin-bottom: 1.5rem;">Reconhecido por Especialistas</h2>
                
                <!-- Partner Institutions Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                    {partner_logos_html}
                </div>

                <!-- Institutional Testimonials -->
                <div style="margin-top: 2rem;">
                    <h3 style="text-align: center; color: #1B365D; margin-bottom: 1.5rem;">O que dizem os especialistas</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                        {institutional_testimonials_html}
                    </div>
                </div>
            </div>
        """.format(
            partner_logos_html=''.join([
                f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{partner['logo']}</div>
                    <h4 style="margin: 0.5rem 0; color: #1B365D;">{partner['name']}</h4>
                    <p style="margin: 0; color: #666; font-size: 0.9em;">{partner['description']}</p>
                </div>
                """ for partner in content['partner_institutions']
            ]),
            institutional_testimonials_html=''.join([
                f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <p style="font-style: italic; margin-bottom: 1rem;">"{testimonial['text']}"</p>
                    <div>
                        <strong style="color: #1B365D;">{testimonial['author']}</strong>
                        <br>
                        <small style="color: #666;">{testimonial['role']}</small>
                        <br>
                        <small style="color: #666;">{testimonial['institution']}</small>
                    </div>
                </div>
                """ for testimonial in content['institutional_testimonials']
            ])
        ), unsafe_allow_html=True)

        # Platform Promotion
        st.markdown('''
            <div style="background-color: #1B365D; color: white; padding: 2rem; border-radius: 8px; text-align: center; margin: 2rem 0;">
                <h2 style="color: white;">Conheça a Ativa-Mente</h2>
                <p style="font-size: 1.1em; margin: 1rem 0;">
                    Plataforma completa de treinamento cognitivo com:
                    <br>• 6+ Jogos Interativos (Memória, Padrões, Foco e mais)
                    <br>• Sistema de Progresso com Níveis
                    <br>• Dicas Diárias Personalizadas
                    <br>• Acompanhamento de Evolução
                    <br>• Histórias de Sucesso Inspiradoras
                </p>
                <div style="background-color: #FFA500; padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem;">
                    <h3 style="color: #1B365D; margin: 0; font-size: 1.5em;">Oferta Especial</h3>
                    <p style="margin: 0.5rem 0; font-size: 1.2em;">
                        <strong>R$ 37,00</strong> - Acesso Vitalício
                        <br>
                        <span style="font-size: 0.9em;">Inclui todos os jogos e atualizações futuras</span>
                    </p>
                    <button style="background-color: #1B365D; color: white; border: none; padding: 0.75rem 2rem; border-radius: 25px; margin-top: 1rem; font-weight: bold; cursor: pointer;">
                        Começar Agora
                    </button>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        # Clinical Recommendation
        recommendation = get_recommendation(scores)
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin: 1.5rem 0;">
            <h3 style="margin: 0 0 1rem 0;">Recomendação Clínica</h3>
            <p style="margin: 0;">{}</p>
        </div>
        """.format(recommendation), unsafe_allow_html=True)
        
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
        
        st.markdown("<h2 style='text-align: center; font-size: 20px;'>Comece sua jornada com a Ativa-Mente</h2>", unsafe_allow_html=True)
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
st.markdown("<p style='text-align: center; padding: 2rem 0;'>Desenvolvido com ❤️ pela Ativa-Mente | Este questionário não substitui uma avaliação profissional</p>", unsafe_allow_html=True)