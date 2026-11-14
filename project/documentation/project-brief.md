# Cirurgia Controle

## Problema e objetivo
Uma organização com várias unidades precisa distinguir o preço de venda de uma cirurgia, o custo previsto dos recursos e o custo realmente registado. Folhas separadas dificultam preservar valores históricos e explicar desvios. O objetivo é demonstrar uma solução relacional que suporta esse fluxo e permite comparar episódios de forma reproduzível.

## Utilizadores e dados
Administrativo prepara pacientes, profissionais e orçamentos; gestor acompanha preços, aprova e encerra episódios; operador regista consumos. São atores conceptuais de uma demonstração local. Gerem-se unidades, especialidades, médicos, pacientes fictícios, procedimentos, referências de preço, pacotes, recursos, orçamentos e consumos.

## Âmbito incluído
Seleção de unidade; preços avulsos por unidade; consulta de nove pacotes; cadastro de pacientes e médicos; vínculo médico/unidade; orçamento persistente avulso ou de pacote; atribuição da equipa; aprovação; registo de consumo; conclusão/cancelamento; comparação económica; pesquisa e impressão do detalhe.

## Âmbito excluído
Autenticação e autorização; publicação na Internet; prontuário clínico; faturação e seguradoras; entidade pagadora separada; stock e fornecedores; séries/lotes de próteses; conflitos de agenda; revisão de orçamento aprovado; estorno ou correção de consumos; edição de pacote pela interface; tabela de preços com vigência temporal. Os catálogos são alteráveis por SQL controlado, com snapshots nas operações.

## Pressupostos
Todos os nomes e valores são fictícios. Há um procedimento por episódio e uma moeda EUR. Paciente e cliente têm o mesmo significado nesta versão. A composição dos nove pacotes é exclusivamente demonstrativa; o catálogo amplo permite orçamento avulso com recursos escolhidos. A elegibilidade médica usa a especialidade do procedimento como simplificação académica, sem validar competências clínicas reais.

## Operação principal
Escolher unidade, paciente, procedimento e modalidade; guardar orçamento e linhas numa transação; atribuir cirurgião; aprovar; inserir consumos; conferir manualmente completude e concluir. Estados terminais não reabrem. O domínio proposto deve ser confirmado pelo grupo com o professor, conforme o guia.
