# Cirurgia Controle

Protótipo local para preparar orçamentos e acompanhar custos cirúrgicos em várias unidades. O projeto demonstra modelação relacional, SQL, integridade de dados e uma aplicação web em Python.

## O que demonstra

- Base de dados SQLite com 17 tabelas, vistas, índices e regras de integridade.
- Catálogo de procedimentos e preços por unidade, com orçamento avulso ou por pacote.
- Registo do custo previsto e dos consumos, preservando preços históricos.
- Aplicação web local sem dependências Python externas.
- Testes e documentação técnica. Os artefactos incluídos registam 69 testes automatizados aprovados na versão documentada do projeto.

## Executar no Windows

1. Instale Python 3.13 ou superior.
2. Extraia o ZIP completo do projeto.
3. Abra a pasta `project` e execute `iniciar.bat`, ou use `py -3.13 application/app.py`.
4. Abra `http://127.0.0.1:8000` no navegador.

A base SQLite e os scripts SQL de demonstração já acompanham o projeto. Para iniciar uma base nova, consulte `project/README.md`.

## Demonstração

A base contém dados fictícios para três unidades. O painel permite escolher uma unidade, consultar orçamentos, comparar valores previstos e consumos e explorar procedimentos e pacotes.

## Limites

Este é um protótipo académico local. Não contém dados de pacientes reais, não tem autenticação, não integra sistemas clínicos e não foi validado para uso clínico ou comercial. Os preços e composições são fictícios. Não exponha o servidor à Internet.

## Trabalho de grupo e uso de IA

O material foi desenvolvido em contexto académico de grupo. Esta cópia pública removeu números de aluno e identificação da capa do relatório; o conjunto de slides da entrega ficou fora da publicação. O projeto documenta o apoio de IA em requisitos, modelação, SQL, implementação, testes e documentação em `project/documentation/ai-use-summary.md`. Consulte esse registo e confirme a sua contribuição individual antes de o descrever no CV.

## Estrutura

- `project/application/` — aplicação Python e testes.
- `project/data/` — esquema, consultas, scripts de demonstração e base SQLite.
- `project/documentation/` — requisitos, regras, dicionário, diagramas, capturas e registos de validação.
- `project/relatorio/Relatorio_Cirurgia_Controle.pdf` — relatório com capa preparada para portefólio.
