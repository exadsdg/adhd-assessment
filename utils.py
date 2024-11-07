import json
from typing import Dict, List

def load_json_data(file_path: str) -> Dict:
    """Load and return JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def calculate_score(responses: Dict[int, str]) -> Dict[str, float]:
    """Calculate scores for each category based on responses."""
    categories = {
        'concentracao': 0,
        'impulsividade': 0,
        'hiperatividade': 0
    }
    
    weights = {
        'Raramente': 0,
        'Às vezes': 1,
        'Frequentemente': 2,
        'Sempre': 3,
        # Custom weights for specific questions
        'Ignora completamente': 3,
        'Perde o foco por alguns minutos': 2,
        'Abandona a atividade': 2,
        'Não consegue retomar o foco': 3,
        'Pensa antes de agir': 0,
        'Age e depois percebe consequências': 1,
        'Age por impulso frequentemente': 2,
        'Não considera consequências': 3,
        'Comunica-se adequadamente': 0,
        'Fala mais que o comum': 1,
        'Domina conversas constantemente': 2,
        'Fala sem parar e fora de contexto': 3
    }
    
    questions = load_json_data('data/questions.json')['questions']
    
    for q in questions:
        if q['id'] in responses:
            score = weights[responses[q['id']]]
            categories[q['category']] += score
    
    # Normalize scores to percentages
    max_score = 3  # Maximum possible score per question
    question_counts = {'concentracao': 0, 'impulsividade': 0, 'hiperatividade': 0}
    for q in questions:
        question_counts[q['category']] += 1
    
    return {k: (v / (max_score * question_counts[k])) * 100 for k, v in categories.items()}

def get_feedback(question: Dict, response: str) -> str:
    """Get appropriate feedback based on response."""
    # Custom mapping for specific questions
    custom_weights = {
        6: {  # Question ID for distractions
            'Ignora completamente': 'high',
            'Perde o foco por alguns minutos': 'medium',
            'Abandona a atividade': 'high',
            'Não consegue retomar o foco': 'high'
        },
        11: {  # Question ID for impulsive decisions
            'Pensa antes de agir': 'low',
            'Age e depois percebe consequências': 'medium',
            'Age por impulso frequentemente': 'high',
            'Não considera consequências': 'high'
        },
        16: {  # Question ID for excessive talking
            'Comunica-se adequadamente': 'low',
            'Fala mais que o comum': 'medium',
            'Domina conversas constantemente': 'high',
            'Fala sem parar e fora de contexto': 'high'
        }
    }
    
    if question['id'] in custom_weights:
        return question['feedback'][custom_weights[question['id']][response]]
    
    # Standard mapping for other questions
    standard_weights = {
        'Raramente': 'low',
        'Às vezes': 'medium',
        'Frequentemente': 'high',
        'Sempre': 'high'
    }
    return question['feedback'][standard_weights[response]]

def get_recommendation(scores: Dict[str, float]) -> str:
    """Generate detailed clinical recommendation based on scores."""
    avg_score = sum(scores.values()) / len(scores)
    max_category = max(scores.items(), key=lambda x: x[1])
    
    if avg_score >= 70:
        return f"""
        Com base no perfil clínico apresentado (média de {avg_score:.1f}%), recomendamos fortemente uma avaliação profissional especializada em TDAH. 
        Os indicadores são particularmente significativos na área de {max_category[0]} ({max_category[1]:.1f}%).
        A Ativa-Mente pode ser uma ferramenta complementar valiosa no processo terapêutico, oferecendo suporte estruturado ao desenvolvimento do seu filho.
        """
    elif avg_score >= 40:
        return f"""
        O perfil apresentado (média de {avg_score:.1f}%) sugere a presença de alguns comportamentos que merecem atenção profissional. 
        A área de {max_category[0]} ({max_category[1]:.1f}%) apresenta os indicadores mais relevantes.
        Recomendamos considerar uma avaliação profissional e utilizar a Ativa-Mente como ferramenta de suporte no desenvolvimento de habilidades específicas.
        """
    else:
        return f"""
        O perfil atual (média de {avg_score:.1f}%) indica comportamentos majoritariamente típicos para a faixa etária.
        Mesmo com indicadores dentro da normalidade, a Ativa-Mente pode contribuir para o desenvolvimento contínuo de habilidades cognitivas e comportamentais.
        """

def get_category_description(category: str, severity: str) -> str:
    """Get detailed clinical description for each category based on severity."""
    descriptions = {
        'concentracao': {
            'Muito Alto': """
                Apresenta déficit significativo na função executiva de atenção sustentada e seletiva.
                Manifestações clínicas incluem:
                - Dificuldade acentuada em manter foco em tarefas estruturadas
                - Comprometimento na filtragem de estímulos irrelevantes
                - Prejuízo significativo na organização e conclusão de tarefas
                - Alta susceptibilidade à distração por estímulos externos
                Recomenda-se avaliação neuropsicológica completa.
            """,
            'Alto': """
                Demonstra desafios importantes na manutenção da atenção e processamento executivo.
                Características observadas:
                - Dificuldade frequente em sustentar atenção em tarefas
                - Comprometimento na conclusão de atividades sequenciais
                - Tendência a perder materiais e objetos importantes
                - Desorganização em atividades cotidianas
            """,
            'Moderado': """
                Apresenta alguns desafios no controle atencional que podem impactar o desempenho.
                Aspectos observados:
                - Oscilação na manutenção do foco
                - Necessidade de suporte na organização de tarefas
                - Eventual dificuldade com instruções complexas
            """,
            'Baixo': """
                Mantém níveis adequados de atenção e organização.
                Características positivas:
                - Boa capacidade de manter foco em tarefas
                - Habilidade adequada de organização
                - Processamento eficiente de instruções
            """
        },
        'impulsividade': {
            'Muito Alto': """
                Apresenta comprometimento significativo no controle inibitório comportamental.
                Manifestações clínicas incluem:
                - Dificuldade acentuada em esperar sua vez
                - Interrupções frequentes em contextos sociais
                - Tomada de decisão sem análise de consequências
                - Respostas precipitadas em situações diversas
                Recomenda-se avaliação especializada em regulação comportamental.
            """,
            'Alto': """
                Demonstra desafios importantes no autocontrole e regulação comportamental.
                Características observadas:
                - Dificuldade em controlar respostas imediatas
                - Tendência a agir sem reflexão prévia
                - Interrupções frequentes em interações sociais
                - Desafios na regulação emocional
            """,
            'Moderado': """
                Apresenta alguns comportamentos impulsivos que podem ser trabalhados.
                Aspectos observados:
                - Ocasional dificuldade em esperar sua vez
                - Algumas decisões sem planejamento adequado
                - Momentos de interrupção em conversas
            """,
            'Baixo': """
                Demonstra bom controle sobre comportamentos impulsivos.
                Características positivas:
                - Adequada capacidade de espera
                - Boa regulação em interações sociais
                - Tomada de decisão reflexiva
            """
        },
        'hiperatividade': {
            'Muito Alto': """
                Apresenta níveis clinicamente significativos de atividade motora excessiva.
                Manifestações clínicas incluem:
                - Agitação motora constante e invasiva
                - Inquietação significativa em situações estruturadas
                - Dificuldade acentuada em atividades que exigem quietude
                - Verbalização excessiva e descontextualizada
                Recomenda-se avaliação especializada em regulação psicomotora.
            """,
            'Alto': """
                Demonstra níveis elevados de atividade motora que impactam o funcionamento.
                Características observadas:
                - Inquietação frequente em diversos contextos
                - Dificuldade em permanecer sentado quando necessário
                - Tendência a falar excessivamente
                - Movimento constante em situações inadequadas
            """,
            'Moderado': """
                Apresenta alguns padrões de inquietação que podem ser regulados.
                Aspectos observados:
                - Momentos de agitação em situações específicas
                - Ocasional dificuldade com atividades calmas
                - Níveis de energia acima da média
            """,
            'Baixo': """
                Mantém níveis adequados de atividade motora e regulação.
                Características positivas:
                - Boa capacidade de autorregulação motora
                - Participação adequada em atividades calmas
                - Controle apropriado da energia física
            """
        }
    }
    return descriptions[category][severity].strip()
