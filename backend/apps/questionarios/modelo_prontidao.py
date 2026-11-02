"""Modelo de prontidão organizacional para IA: 5 dimensões, 19 fatores (Quadro 11) e 38 itens.

PROVISÓRIO: os itens foram redigidos a partir das definições dos fatores e ainda passarão pela
validação de conteúdo com os especialistas. Os pesos das dimensões são proporcionais ao número de
fatores de cada uma, até o modelo definir pesos próprios.

v1.1: redação e relevância revisadas pelo orientador; sete itens passam a ser afirmações negativas
(marcados com Invertida), que entram no cálculo com a escala espelhada.
"""

VERSAO = '1.1-provisorio'


class Invertida(str):
    """Item com afirmação negativa: concordar indica menor prontidão."""


# (código, nome, descrição, peso, pergunta aberta, [(fator, definição, [item, item])])
DIMENSOES = [
    ('tecnologia', 'Tecnologia', 'Infraestrutura, integração e percepção da tecnologia de IA.', 3,
     'Descreva os principais sistemas e a infraestrutura de TI que a empresa usa hoje.', [
         ('Infraestrutura e recursos de TI',
          'Existência e adequação da infraestrutura tecnológica, ativos e recursos de TI', [
              'Nossa organização possui infraestrutura computacional (nuvem ou local) capaz de suportar o '
              'processamento de cargas de trabalho pesadas de IA.',
              'A empresa consegue ampliar seus recursos de computação quando um projeto precisa.',
          ]),
         ('Compatibilidade, integração e arquitetura',
          'Encaixe técnico da IA com sistemas, processos e arquitetura existentes', [
              'Os sistemas da organização conseguem trocar dados com novas aplicações, como soluções de IA, '
              'sem grandes adaptações.',
              'Uma solução de IA poderia ser integrada aos sistemas atuais sem grandes reconstruções.',
          ]),
         ('Vantagem relativa e complexidade percebida',
          'Benefício percebido da IA em relação à situação atual e sua complexidade', [
              'A empresa enxerga benefícios claros da IA em comparação com as soluções que já usa.',
              'A equipe de TI considera viável adotar IA com a capacidade técnica que tem hoje.',
          ]),
     ]),
    ('organizacao', 'Organização', 'Recursos, processos, cultura e colaboração da organização.', 5,
     'Como a empresa costuma conduzir mudanças e novos projetos?', [
         ('Recursos financeiros e orçamento',
          'Disponibilidade de recursos (financeiros, orçamento dedicado, pessoal) para iniciativas de IA', [
              'A IA é tratada como um investimento estratégico contínuo, com orçamento garantido para custos de '
              'sustentação, licenças e infraestrutura.',
              'A empresa consegue destinar pessoas e tempo a projetos de IA.',
          ]),
         ('Processos e fluxos de trabalho',
          'Processos, atividades e estrutura organizacional preparados para incorporar a IA', [
              'Os principais processos operacionais da organização estão documentados e são executados de forma '
              'padronizada.',
              'Os fluxos de trabalho podem ser ajustados para incorporar novas ferramentas.',
          ]),
         ('Cultura de inovação e aprendizagem',
          'Inovatividade, abertura à inovação, aprendizagem organizacional e atitude frente ao risco', [
              Invertida('As equipes evitam testar novas soluções por medo de serem punidas se o teste não der '
                        'certo.'),
              'Erros em projetos novos são tratados como oportunidade de aprendizado.',
          ]),
         ('Gestão da mudança e abertura à mudança',
          'Capacidade de conduzir mudanças e obstáculos a elas', [
              'A organização já conduziu com sucesso mudanças importantes na forma de trabalhar, como a adoção de '
              'novos sistemas ou processos.',
              'As equipes costumam aceitar bem mudanças na forma de trabalhar.',
          ]),
         ('Colaboração entre áreas',
          'Trabalho colaborativo e parcerias entre unidades de IA/dados e áreas de negócio', [
              'As áreas de negócio e de tecnologia trabalham juntas nos projetos.',
              Invertida('As áreas da empresa trabalham de forma isolada (silos), dificultando a troca de '
                        'informações e o trabalho conjunto para iniciativas de IA.'),
          ]),
     ]),
    ('dados', 'Dados', 'Qualidade, governança e acesso aos dados.', 3,
     'Descreva onde ficam os principais dados da empresa e como eles são usados.', [
         ('Qualidade e confiabilidade',
          'Qualidade, confiabilidade e representatividade dos dados', [
              Invertida('As bases de dados do sistema contêm inconsistências graves, dados duplicados ou omissões '
                        'que comprometem o treino de inteligências artificiais.'),
              'A empresa confia nos próprios dados para tomar decisões.',
          ]),
         ('Gestão e governança',
          'Práticas de gestão, governança da informação e registro sistemático dos dados', [
              'A organização conta com catálogo de dados, dicionários padronizados e controle rigoroso de '
              'permissões e acessos por perfil.',
              'A organização tem regras definidas sobre quem pode usar quais dados e para quais finalidades.',
          ]),
         ('Disponibilidade e acessibilidade',
          'Existência, volume e acesso aos dados necessários', [
              'A empresa tem dados suficientes sobre os processos que deseja melhorar com IA.',
              'Os dados das diferentes áreas de negócio estão centralizados em repositórios acessíveis '
              '(Data Lakes/Warehouses), evitando silos isolados.',
          ]),
     ]),
    ('conhecimento', 'Conhecimento', 'Competências, capacitação e entendimento sobre IA.', 3,
     'Que conhecimento sobre IA a equipe tem hoje e como ela costuma aprender coisas novas?', [
         ('Competências e habilidades da equipe',
          'Pessoal qualificado, habilidades técnicas e digitais e capacidade humana disponível', [
              'A organização conta com profissionais, da própria equipe ou de parceiros, capazes de desenvolver '
              'ou adaptar soluções de IA.',
              Invertida('A equipe de TI não possui conhecimento técnico básico para desenvolver, customizar ou '
                        'consumir integrações e modelos de IA.'),
          ]),
         ('Capacitação e treinamento',
          'Programas de treinamento e desenvolvimento', [
              'A empresa oferece oportunidades de capacitação dos colaboradores no uso de IA.',
              'As pessoas têm tempo e incentivo para aprender novas competências.',
          ]),
         ('Conscientização e letramento em IA',
          'Entendimento sobre o que é a IA, seus usos e limites', [
              'Os gestores das áreas de negócio entendem o que a IA pode e o que não pode fazer.',
              Invertida('Os líderes de negócio desconhecem as aplicações da IA e demonstram receio ou '
                        'desconfiança de que a automação substituirá suas funções.'),
          ]),
     ]),
    ('estrategia', 'Estratégia', 'Liderança, oportunidades, plano e alinhamento da IA ao negócio.', 5,
     'Que problemas de negócio a empresa espera resolver com IA?', [
         ('Apoio e comprometimento da liderança',
          'Apoio da alta gestão e comprometimento com iniciativas de IA', [
              'A alta gestão apoia abertamente as iniciativas de IA.',
              Invertida('A alta liderança trata a IA como um custo, e não como um investimento.'),
          ]),
         ('Caso de negócio e identificação de oportunidades',
          'Potencial de negócio, casos de uso, oportunidades e análise econômica que justificam a IA', [
              'A empresa identificou problemas de negócio em que a IA pode gerar valor.',
              Invertida('Os projetos de IA na organização são iniciados por modismo, sem metas claras de retorno '
                        'sobre o investimento (ROI) ou redução de custos.'),
          ]),
         ('Estratégia, visão e plano de IA',
          'Existência de estratégia, visão, objetivos, política ou roadmap para IA', [
              'A organização possui uma estratégia ou um plano de IA documentado.',
              'As iniciativas de IA têm objetivos e metas definidos.',
          ]),
         ('Alinhamento IA-negócio',
          'Coerência entre as iniciativas de IA e a estratégia e os objetivos do negócio', [
              'As iniciativas de IA da organização, em andamento ou planejadas, estão ligadas a objetivos de '
              'negócio definidos.',
              'As áreas de negócio participam da definição das prioridades de IA.',
          ]),
         ('Adequação da IA aos processos',
          'Avaliação de quais processos se beneficiam da IA e da compatibilidade com eles', [
              'A empresa avaliou quais processos se beneficiariam de IA.',
              'Os principais processos da organização têm etapas bem definidas, do início ao fim.',
          ]),
     ]),
]
