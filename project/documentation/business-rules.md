# Regras de negócio da versão 1.0

| ID | Regra | Implementação |
| --- | --- | --- |
| BR01 | Cada episódio pertence a uma unidade, um paciente e um procedimento. | FK, NOT NULL e bloqueio da identificação do episódio. |
| BR02 | Associações N:M não aceitam identificadores nulos nem pares repetidos. | NOT NULL, FK e PK composta. |
| BR03 | O preço avulso depende do par unidade/procedimento. | PK composta em unit_procedure_price; consulta parametrizada. |
| BR04 | O pacote escolhido corresponde à unidade e ao procedimento do episódio. | Serviço e trigger budget_package_insert. |
| BR05 | Orçamento avulso não tem pacote; orçamento de pacote identifica o pacote. | CHECK em budget. |
| BR06 | A aprovação exige linhas e episódio agendado; existe no máximo um aprovado por episódio. | Triggers e índice único parcial. |
| BR07 | Orçamento aprovado e as suas linhas são imutáveis. | Triggers de INSERT, UPDATE e DELETE. |
| BR08 | Consumo exige aprovação e episódio agendado ou em curso; a primeira inserção inicia o episódio. | Triggers consumption_allowed e consumption_starts_surgery. |
| BR09 | Consumos não podem ser alterados ou apagados nesta versão. | Triggers, incluindo UPDATE e DELETE. |
| BR10 | Estados terminais não reabrem; agendada passa a em_curso ou cancelada; em_curso passa a concluida. | Triggers surgery_initial, surgery_transition e surgery_start. |
| BR11 | A conclusão exige um consumo e um cirurgião atribuído. | Trigger surgery_finish. A conferência de completude dos consumos é manual. |
| BR12 | Médico atribuído tem a especialidade do procedimento e vínculo à unidade. | Trigger team_eligible, bloqueio de UPDATE dos vínculos/especialidades usados e participações imutáveis. |
| BR13 | Quantidades são positivas, até um milhão e com até três casas; custos são não negativos. | CHECK e validação Decimal na aplicação. |
| BR14 | Arredondar cada linha ao cêntimo, metade para cima, antes de somar. | ROUND de produtos não negativos em ambas as views. |
| BR15 | Atualizações do catálogo não reavaliam preços e custos históricos. | Snapshots em budget, budget_line e consumption. |
| BR16 | Criação de episódio, orçamento e linhas é atómica. | Contexto transacional; rollback confirmado após inserção parcial. |

As políticas de interface validam também o unit_id nos pedidos. A seleção de unidade é contexto operacional, não autorização de segurança. Não se faz gestão de conflitos de agenda.
