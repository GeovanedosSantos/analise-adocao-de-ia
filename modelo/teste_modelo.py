import asyncio
import httpx

MODEL_SERVICE_URL = "http://localhost:8000/api/v1/model/evaluate"

PAYLOAD_SUBDIMENSOES_EXEMPLO = {
    "empresa_nome": "InovaTech Corp",
    "contexto_qualitativo": "Empresa do setor financeiro migrando de sistemas legados para microsserviços em nuvem com foco em IA.",
    "respostas": {
        "tecnologia": {
            "infraestrutura_cloud": [5, 4, 5],     # Média: 4.67 -> Nota: 91.67
            "sistemas_legados": [2, 1, 2],         # Média: 1.67 -> Nota: 16.67 (GARGALO!)
            "ferramental_mlops": [3, 4, 3]         # Média: 3.33 -> Nota: 58.33
        },
        "organizacao": {
            "suporte_lideranca": [4, 5],            # Média: 4.5 -> Nota: 87.5
            "cultura_risco": [2, 3],               # Média: 2.5 -> Nota: 37.5
            "governanca_etica": [4, 4]              # Média: 4.0 -> Nota: 75.0
        },
        "dados": {
            "qualidade_saneamento": [4, 4, 5],      # Média: 4.33 -> Nota: 83.33
            "arquitetura_acessibilidade": [4, 5],   # Média: 4.5 -> Nota: 87.5
            "governanca_dados": [3, 4, 3]           # Média: 3.33 -> Nota: 58.33
        },
        "conhecimento": {
            "habilidades_tecnicas": [2, 2, 3],      # Média: 2.33 -> Nota: 33.33
            "literacia_negocio": [3, 3],           # Média: 3.0 -> Nota: 50.0
            "programas_upskilling": [1, 2]         # Média: 1.5 -> Nota: 12.5 (GARGALO!)
        },
        "estrategia": {
            "casos_uso_roi": [4, 4],               # Média: 4.0 -> Nota: 75.0
            "orcamento_priorizacao": [3, 4],        # Média: 3.5 -> Nota: 62.5
            "escalabilidade_modelo": [2, 3]         # Média: 2.5 -> Nota: 37.5
        }
    },
    "respostas_dissertativas": {
        "tecnologia": "Temos excelente infraestrutura na AWS, porém o mainframe legado de transações não possui APIs REST e trava o consumo de dados em tempo real.",
        "conhecimento": "Não há nenhum treinamento de IA oferecido para a equipe de produtos ou operações."
    }
}

async def testar_servico_subdimensoes():
    print("=" * 70)
    print("🚀 TESTANDO SERVIÇO DE MODELO COM SUB-DIMENSÕES GRANULARES")
    print("=" * 70)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(MODEL_SERVICE_URL, json=PAYLOAD_SUBDIMENSOES_EXEMPLO)

        if response.status_code == 200:
            dados = response.json()
            print("\n✅ RESPOSTA COM SUCESSO (Status 200 OK):")
            print("-" * 70)
            print(f"• Score Geral: {dados['score_geral']} / 100")
            print(f"• Estágio Gartner: {dados['estagio_gartner']}")
            
            print("\n• Scores por Dimensão Principal:")
            for dim, score in dados["scores_dimensoes"].items():
                print(f"  - {dim.capitalize()}: {score}/100")

            print("\n• Scores Granulares por Sub-Dimensão:")
            for sub, score in dados["scores_subdimensoes"].items():
                alerta = " ⚠️ (Gargalo Critico)" if score < 40 else ""
                print(f"  └─ {sub}: {score}/100{alerta}")

            relatorio = dados.get("relatorio_llm", {})
            print("\n• Diagnóstico do LLM:")
            print(f"  {relatorio.get('diagnostico_geral')}")

            print("\n• Gaps Críticos:")
            for gap in relatorio.get("gaps_criticos", []):
                print(f"  - {gap}")

            print("\n• Plano de Ação Recomendado:")
            for item in relatorio.get("plano_de_acao", []):
                print(f"  [{item['fase']}] ({item['dimensao_foco']}): {item['acao']}")
            print("-" * 70)
        else:
            print(f"\n❌ ERRO NA REQUISIÇÃO (Status {response.status_code}):\n{response.text}")

    except Exception as e:
        print(f"\n❌ ERRO DE CONEXÃO: {str(e)}")

if __name__ == "__main__":
    asyncio.run(testar_servico_subdimensoes())