# CONTEXT_RULES — TaskAnalyzer

Fonte de verdade para qualquer agente de IA que gere código neste repositório.
Contrato de negócio: `specs/task_analyzer_spec.md`.

## 1. Diretrizes arquiteturais (obrigatórias)
- Python 3.11 ou superior.
- Type hints em todas as funções e métodos.
- Single Responsibility (SRP) e PEP 8.
- Docstrings no padrão Google style para módulos, classes e funções.
- Funções pequenas, coesas e com um único propósito.
- Exceções específicas (`TaskValidationError`) com mensagens claras.
- Logs com o módulo `logging` (nunca `print`).
- Nomes descritivos, com idioma consistente em todo o projeto.

## 2. Proibições explícitas
- Não usar bibliotecas externas (apenas biblioteca padrão e `pytest`).
- Não alterar, remover ou adaptar os cenários de teste da especificação.
- Não modificar a estrutura de pastas definida na especificação.
- Não persistir dados em arquivos ou bancos de dados (módulo stateless).
- Não alterar a assinatura das funções públicas sem nova versão da especificação.
- Não gerar código sem os testes correspondentes.
- Não duplicar código (DRY).
- Não assumir comportamentos não especificados: ambiguidades devem ser
  perguntadas ao humano antes da geração, nunca resolvidas por suposição.

## 3. Regras de interação com IA
- Fornecer sempre a especificação e este arquivo antes de pedir código.
- Validar se a IA compreendeu o contrato e os cenários antes de aceitar a solução.
- Solicitar explicações passo a passo em caso de dúvida.
- Revisar criticamente todo código gerado; nunca aceitar "às cegas".
- Rejeitar e pedir nova geração para qualquer violação das seções 1 e 2.
