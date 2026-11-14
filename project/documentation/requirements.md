# Requisitos funcionais da versão 1.0

| ID | Requisito | Ator conceptual | Aceitação |
| --- | --- | --- | --- |
| FR01 | Selecionar uma unidade | Gestor | Painel, preços, pacotes e episódios refletem a unidade escolhida. |
| FR02 | Consultar e atualizar preços avulsos | Gestor | Atualizar o catálogo da unidade sem alterar orçamentos guardados. |
| FR03 | Consultar pacotes e composição | Gestor | Apresentar recursos, quantidades, custo atual e preço de venda por unidade. |
| FR04 | Cadastrar pacientes fictícios | Administrativo | Guardar nome e código único; permitir pesquisa. |
| FR05 | Cadastrar e vincular médicos | Administrativo | Associar profissional a especialidade e unidade; vincular um profissional existente. |
| FR06 | Criar episódio e orçamento | Administrativo | Guardar paciente, unidade, procedimento, data, modalidade e linhas numa transação. |
| FR07 | Atribuir equipa médica | Gestor | Aceitar apenas médicos da unidade e especialidade, antes de iniciar o episódio. |
| FR08 | Aprovar orçamento | Gestor | Aceitar rascunho com linhas em episódio agendado; fixar valores. |
| FR09 | Registar consumos | Operador | Copiar custo unitário atual para o histórico e registar quantidade e motivo opcional. |
| FR10 | Concluir ou cancelar episódio | Gestor | Concluir em curso com cirurgião e consumo; cancelar apenas agendados. |
| FR11 | Analisar custos e margens | Gestor | Apresentar resumo e detalhe com a mesma política de arredondamento; custos abertos são parciais. |
| FR12 | Pesquisar e imprimir | Gestor | Pesquisar nomes, códigos ou estados e imprimir o detalhe através do navegador. |

Os atores descrevem responsabilidades. A aplicação local não implementa autenticação nem permissões por utilizador. Revisão de orçamento aprovado, stock, faturação e integrações são excluídos.
