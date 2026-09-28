from apps.questionarios.models import Dimensao, Pergunta, Questionario, TipoPergunta


def criar_questionario(versao='1.0', publicar=True):
    """Questionário com duas dimensões:

    - Dados (peso 2): duas objetivas (pesos 1 e 3) e uma dissertativa
    - Pessoas (peso 1): uma objetiva (peso 1)
    """
    questionario = Questionario.objects.create(versao=versao)
    dados = Dimensao.objects.create(questionario=questionario, nome='Dados', peso=2, ordem=1)
    pessoas = Dimensao.objects.create(questionario=questionario, nome='Pessoas', peso=1, ordem=2)
    Pergunta.objects.create(dimensao=dados, texto='Os dados são catalogados?', tipo=TipoPergunta.OBJETIVA, peso=1, ordem=1)
    Pergunta.objects.create(dimensao=dados, texto='Há governança de dados?', tipo=TipoPergunta.OBJETIVA, peso=3, ordem=2)
    Pergunta.objects.create(dimensao=dados, texto='Descreva seus dados.', tipo=TipoPergunta.DISSERTATIVA, peso=1, ordem=3)
    Pergunta.objects.create(dimensao=pessoas, texto='A equipe é capacitada?', tipo=TipoPergunta.OBJETIVA, peso=1, ordem=1)
    if publicar:
        questionario.publicar()
    return questionario


def perguntas(questionario, tipo=None):
    qs = Pergunta.objects.filter(dimensao__questionario=questionario).order_by('dimensao__ordem', 'ordem')
    return list(qs.filter(tipo=tipo) if tipo else qs)
