# Uso de IA e validação

## Contexto
Codex apoiou requisitos, modelação, SQL, implementação, testes e documentação. O projeto anterior regista confirmação de validação humana da dupla em 17/10/2026. Essa confirmação refere-se à versão anterior; não representa validação humana automática das alterações de 19/10. A nova versão tem evidência técnica e deve ser compreendida e revista pelo grupo antes da defesa.

## AI01 Preservar preços históricos
Entrada: guia, problema e regras; tarefa: distinguir venda, previsão e realização. Saída: snapshots em budget, budget_line e consumption. Risco: usar o custo atual para reavaliar episódios antigos. Decisão: guardar valores na operação e testar atualização do catálogo sem alterar o episódio 1. Evidência: test_historical_price e test_reference_totals.

## AI02 Corrigir lacunas de integridade
Entrada: auditoria, DDL e suite anterior. Tarefa: testar operações inválidas além dos casos existentes. Problema encontrado: PK compostas aceitavam NULL; consumos concluídos aceitavam UPDATE/DELETE; estados concluídos reabriam. Correção: NOT NULL e triggers, com regressões que rejeitam as quatro famílias de operações. Evidência: test_null_composite_keys, test_closed_consumption_update/delete e test_reopen_closed. A revisão técnica foi executada pela IA; o grupo pode repetir os comandos documentados.

## AI03 Incorporar múltiplas unidades
Entrada: pedido do aluno, artefactos validados e âmbito. Tarefa: adicionar seletor de unidade, preços avulsos e pacotes. Problema considerado: filtro visual isolado permitiria usar pacote ou episódio de outra unidade. Decisão: unidade explícita em surgery/package e preço por par unidade/procedimento; verificações no serviço e trigger de compatibilidade de pacote. Evidência: testes cross_unit, wrong_package e doctor_unit. O contexto de unidade não foi apresentado como autenticação.

## AI04 Validar dinheiro e interface
Entrada: views e aplicação. Problemas encontrados: arredondamento da soma divergia do arredondamento por recurso; a seleção automática de pacote ficava vazia após escolher procedimento. Correção: arredondamento por linha em ambas as views; seleção de primeira opção compatível quando não existe seleção. Evidência: test_rounding_detail_equals_summary, test_all_detail_totals e fluxo real no navegador numa cópia da base. Os 32 testes aprovados não substituem a conferência humana do domínio e da defesa.


## Verificação alargada

Além das 32 regressões, passaram 37 testes adicionais de serviços e HTTP: 69 no total. A revisão acrescentou tabelas STRICT, três proteções de alteração de vínculos e especialidade, datas locais com minutos e respostas controladas para episódios sem orçamento ou identificadores fora do intervalo. O ficheiro acceptance-results.json regista a suite adicional. browser-acceptance.json descreve cadastros, preços, avulso, pacote, cancelamento, erros de formulário e ecrã pequeno, todos numa cópia independente. Não foi testada uma impressora física.
