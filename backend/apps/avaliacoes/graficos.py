"""Gráficos do relatório em PDF (RF15), em SVG: o WeasyPrint desenha SVG sem depender de JavaScript."""

import math
from html import escape

COR_ATUAL = '#4f46e5'
COR_ANTERIOR = '#c8641a'
COR_GRADE = '#e5e7eb'
COR_TEXTO = '#4b5563'


def radar(eixos, atual, anterior=None, tamanho=260):
    """Radar de 0 a 100. `eixos`: nomes; `atual` e `anterior`: notas na mesma ordem (None = sem nota)."""
    if len(eixos) < 3:
        return ''  # radar com menos de 3 eixos não forma área
    # Sobra largura dos lados para os nomes dos eixos não serem cortados
    largura = tamanho + 120
    centro_x, centro, raio = largura / 2, tamanho / 2, tamanho / 2 - 30

    def ponto(i, valor):
        angulo = -math.pi / 2 + 2 * math.pi * i / len(eixos)
        r = raio * max(0, min(valor, 100)) / 100
        return centro_x + r * math.cos(angulo), centro + r * math.sin(angulo)

    def poligono(valores, cor, opacidade):
        pontos = ' '.join(f'{x:.1f},{y:.1f}' for x, y in (ponto(i, v or 0) for i, v in enumerate(valores)))
        return f'<polygon points="{pontos}" fill="{cor}" fill-opacity="{opacidade}" stroke="{cor}" stroke-width="2"/>'

    partes = []
    for nivel in (25, 50, 75, 100):
        pontos = ' '.join(f'{x:.1f},{y:.1f}' for x, y in (ponto(i, nivel) for i in range(len(eixos))))
        partes.append(f'<polygon points="{pontos}" fill="none" stroke="{COR_GRADE}"/>')
    for i, nome in enumerate(eixos):
        x, y = ponto(i, 100)
        partes.append(f'<line x1="{centro_x}" y1="{centro}" x2="{x:.1f}" y2="{y:.1f}" stroke="{COR_GRADE}"/>')
        lx, ly = ponto(i, 112)
        ancora = 'middle' if abs(lx - centro_x) < 10 else ('start' if lx > centro_x else 'end')
        partes.append(
            f'<text x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="{ancora}" font-size="10" fill="{COR_TEXTO}">'
            f'{escape(nome)}</text>'
        )
    if anterior and any(v is not None for v in anterior):
        partes.append(poligono(anterior, COR_ANTERIOR, 0.08))
    partes.append(poligono(atual, COR_ATUAL, 0.18))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{tamanho}">{"".join(partes)}</svg>'


def linha_do_tempo(pontos, largura=300, altura=200):
    """Índice geral ao longo das avaliações. `pontos`: [(rótulo da data, nota)] em ordem cronológica."""
    if len(pontos) < 2:
        return ''
    # Margem direita larga o bastante para a última data, centralizada no último ponto
    esquerda, direita, topo, base = 34, 26, 12, 28
    util_x, util_y = largura - esquerda - direita, altura - topo - base

    def xy(i, nota):
        return esquerda + util_x * i / (len(pontos) - 1), topo + util_y * (1 - nota / 100)

    partes = []
    for nivel in (0, 25, 50, 75, 100):
        _, y = xy(0, nivel)
        partes.append(f'<line x1="{esquerda}" y1="{y:.1f}" x2="{largura - direita}" y2="{y:.1f}" stroke="{COR_GRADE}"/>')
        partes.append(f'<text x="{esquerda - 6}" y="{y + 3:.1f}" text-anchor="end" font-size="9" fill="{COR_TEXTO}">{nivel}</text>')
    caminho = ' '.join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(xy(i, n) for i, (_, n) in enumerate(pontos)))
    partes.append(f'<path d="{caminho}" fill="none" stroke="{COR_ATUAL}" stroke-width="2"/>')
    for i, (rotulo, nota) in enumerate(pontos):
        x, y = xy(i, nota)
        partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{COR_ATUAL}"/>')
        partes.append(f'<text x="{x:.1f}" y="{altura - 8}" text-anchor="middle" font-size="9" fill="{COR_TEXTO}">{escape(rotulo)}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}">{"".join(partes)}</svg>'
