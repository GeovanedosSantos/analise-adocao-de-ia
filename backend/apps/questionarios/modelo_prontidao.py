"""Modelo de prontidão organizacional para IA: 5 dimensões, 19 fatores (Quadro 11) e 38 itens.

PROVISÓRIO: os itens foram redigidos a partir das definições dos fatores e ainda passarão pela
validação de conteúdo com os especialistas. Os pesos das dimensões são proporcionais ao número de
fatores de cada uma, até o modelo definir pesos próprios.
"""

VERSAO = '1.0-provisorio'

# (código, nome, descrição, peso, pergunta aberta, [(fator, definição, [item, item])])
DIMENSOES = [
    ('tecnologia', 'Tecnologia', 'Infraestrutura, integração e percepção da tecnologia de IA.', 3,
     'Descreva os principais sistemas e a infraestrutura de TI que a empresa usa hoje.', [
         ('Infraestrutura e recursos de TI',
          'Existência e adequação da infraestrutura tecnológica, ativos e recursos de TI', [
              'A empresa tem infraestrutura de TI (servidores, nuvem, armazenamento) capaz de suportar soluções de IA.',
              'A empresa consegue ampliar seus recursos de computação quando um projeto precisa.',
          ]),
         ('Compatibilidade, integração e arquitetura',
          'Encaixe técnico da IA com sistemas, processos e arquitetura existentes', [
              'Os sistemas atuais conseguem trocar dados com novas ferramentas, por exemplo por meio de APIs.',
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
              'Existe orçamento reservado para iniciativas de IA.',
              'A empresa consegue destinar pessoas e tempo a projetos de IA.',
          ]),
         ('Processos e fluxos de trabalho',
          'Processos, atividades e estrutura organizacional preparados para incorporar a IA', [
              'Os principais processos da empresa estão documentados e padronizados.',
              'Os fluxos de trabalho podem ser ajustados para incorporar novas ferramentas.',
          ]),
         ('Cultura de inovação e aprendizagem',
          'Inovatividade, abertura à inovação, aprendizagem organizacional e atitude frente ao risco', [
              'A empresa incentiva testar ideias novas, mesmo com risco de não dar certo.',
              'Erros em projetos novos são tratados como oportunidade de aprendizado.',
          ]),
         ('Gestão da mudança e abertura à mudança',
          'Capacidade de conduzir mudanças e obstáculos a elas', [
              'A empresa tem experiência em conduzir mudanças em funções e rotinas de trabalho.',
              'As equipes costumam aceitar bem mudanças na forma de trabalhar.',
          ]),
         ('Colaboração entre áreas',
          'Trabalho colaborativo e parcerias entre unidades de IA/dados e áreas de negócio', [
              'As áreas de negócio e de tecnologia trabalham juntas nos projetos.',
              'Os departamentos compartilham informações entre si sem grandes barreiras.',
          ]),
     ]),
    ('dados', 'Dados', 'Qualidade, governança e acesso aos dados.', 3,
     'Descreva onde ficam os principais dados da empresa e como eles são usados.', [
         ('Qualidade e confiabilidade',
          'Qualidade, confiabilidade e representatividade dos dados', [
              'Os dados da empresa são corretos, completos e atualizados.',
              'A empresa confia nos próprios dados para tomar decisões.',
          ]),
         ('Gestão e governança',
          'Práticas de gestão, governança da informação e registro sistemático dos dados', [
              'Há responsáveis definidos pelos principais conjuntos de dados.',
              'Existem regras para coletar, armazenar e proteger os dados.',
          ]),
         ('Disponibilidade e acessibilidade',
          'Existência, volume e acesso aos dados necessários', [
              'A empresa tem dados suficientes sobre os processos que deseja melhorar com IA.',
              'Quem precisa dos dados consegue acessá-los sem grande esforço.',
          ]),
     ]),
    ('conhecimento', 'Conhecimento', 'Competências, capacitação e entendimento sobre IA.', 3,
     'Que conhecimento sobre IA a equipe tem hoje e como ela costuma aprender coisas novas?', [
         ('Competências e habilidades da equipe',
          'Pessoal qualificado, habilidades técnicas e digitais e capacidade humana disponível', [
              'A empresa tem pessoas com conhecimento técnico para desenvolver ou operar soluções de IA.',
              'As equipes têm habilidades digitais para usar ferramentas de IA no dia a dia.',
          ]),
         ('Capacitação e treinamento',
          'Programas de treinamento e desenvolvimento', [
              'A empresa oferece treinamentos sobre IA ou dados.',
              'As pessoas têm tempo e incentivo para aprender novas competências.',
          ]),
         ('Conscientização e letramento em IA',
          'Entendimento sobre o que é a IA, seus usos e limites', [
              'As lideranças entendem o que a IA pode e o que não pode fazer.',
              'As equipes conhecem os riscos do uso de IA, como erros e vieses.',
          ]),
     ]),
    ('estrategia', 'Estratégia', 'Liderança, oportunidades, plano e alinhamento da IA ao negócio.', 5,
     'Que problemas de negócio a empresa espera resolver com IA?', [
         ('Apoio e comprometimento da liderança',
          'Apoio da alta gestão e comprometimento com iniciativas de IA', [
              'A alta gestão apoia abertamente as iniciativas de IA.',
              'A alta gestão se compromete a dar recursos e acompanhar os projetos de IA.',
          ]),
         ('Caso de negócio e identificação de oportunidades',
          'Potencial de negócio, casos de uso, oportunidades e análise econômica que justificam a IA', [
              'A empresa identificou problemas de negócio em que a IA pode gerar valor.',
              'Os casos de uso de IA são avaliados quanto a custo e retorno antes de serem aprovados.',
          ]),
         ('Estratégia, visão e plano de IA',
          'Existência de estratégia, visão, objetivos, política ou roadmap para IA', [
              'Existe uma estratégia ou plano formal para o uso de IA.',
              'As iniciativas de IA têm objetivos e metas definidos.',
          ]),
         ('Alinhamento IA-negócio',
          'Coerência entre as iniciativas de IA e a estratégia e os objetivos do negócio', [
              'As iniciativas de IA estão ligadas aos objetivos estratégicos da empresa.',
              'As áreas de negócio participam da definição das prioridades de IA.',
          ]),
         ('Adequação da IA aos processos',
          'Avaliação de quais processos se beneficiam da IA e da compatibilidade com eles', [
              'A empresa avaliou quais processos se beneficiariam de IA.',
              'A empresa sabe em quais processos a IA não deve ser aplicada.',
          ]),
     ]),
]
