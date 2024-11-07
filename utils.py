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
        'Sempre': 3
    }
    
    questions = load_json_data('data/questions.json')['questions']
    
    for q in questions:
        if q['id'] in responses:
            score = weights[responses[q['id']]]
            categories[q['category']] += score
    
    # Normalize scores to percentages
    max_score = 3  # Maximum possible score per category
    return {k: (v / max_score) * 100 for k, v in categories.items()}

def get_feedback(question: Dict, response: str) -> str:
    """Get appropriate feedback based on response."""
    weights = {
        'Raramente': 'low',
        'Às vezes': 'medium',
        'Frequentemente': 'high',
        'Sempre': 'high'
    }
    return question['feedback'][weights[response]]

def get_recommendation(scores: Dict[str, float]) -> str:
    """Generate recommendation based on scores."""
    avg_score = sum(scores.values()) / len(scores)
    
    if avg_score >= 70:
        return "Com base nas suas respostas, recomendamos fortemente uma avaliação profissional para TDAH. A Ativa-Mente pode ser uma ferramenta valiosa no suporte ao desenvolvimento do seu filho."
    elif avg_score >= 40:
        return "Alguns comportamentos indicam que seu filho poderia se beneficiar do suporte adicional oferecido pela Ativa-Mente. Considere uma avaliação profissional."
    else:
        return "Seu filho parece apresentar comportamentos típicos para a idade. A Ativa-Mente ainda pode ajudar no desenvolvimento de habilidades importantes."
