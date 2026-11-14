# Resultado da verificação completa

Revisão de 19/10/2026. Foram executados **69 testes automáticos**, divididos em 32 regressões e 37 verificações adicionais de serviços/HTTP. Todos passaram após as correções. Resultados: test-results.json e acceptance-results.json.

## Cobertura executada

| Área | Verificação |
|---|---|
| Navegação | Seis páginas nas três unidades; rotas desconhecidas; CSS; detalhe e pesquisa sem resultados |
| Cadastros | Paciente e médico; vínculo à unidade; unicidade; campos vazios; reversão de cadastro médico inválido |
| Preços | Atualização só na unidade escolhida; centavos exatos; novo preço em orçamento futuro; pacote independente |
| Orçamentos | Criação avulsa e por pacote; incompatibilidades; linhas vazias/duplicadas; aprovação inexistente/repetida |
| Transação | Reversão após inserir parte do episódio/orçamento; nenhuma linha órfã |
| Equipa | Especialidade, unidade e estado; rejeição após início; proteção de alterações posteriores dos catálogos usados |
| Consumos | Aprovação obrigatória; quantidades e motivos; conclusão e cancelamento; imutabilidade |
| Estados | Bloqueio de reabertura e transições inválidas; conclusão com cirurgião e consumo |
| Dinheiro | Snapshots históricos; arredondamento por linha; múltiplos consumos do mesmo recurso; resumo igual ao detalhe |
| SQL | Tipagem STRICT; PK/FK/NOT NULL; integridade; resultados esperados das consultas e totais por unidade |
| HTTP | Respostas 200/303/400/404; identificadores excessivos; UTF-8 inválido; campos ausentes; tentativas entre unidades; texto HTML escapado |
| Apresentação em ecrã pequeno | Seis páginas sem alargamento horizontal do documento; tabelas com deslocação interna |
| Entrega | ZIP, hashes, reconstrução SQL e execução das duas suites na instalação extraída |

## Fluxos reais no navegador

Todos executados numa base de testes separada, sem acrescentar pessoas ou cirurgias à entrega.

1. Cadastrar e pesquisar paciente; cadastrar médico e vincular outro profissional à unidade Porto.
2. Alterar o preço avulso do joelho para 7 777,77 EUR no Porto.
3. Criar orçamento avulso, atribuir médico, aprovar, inserir quatro recursos e concluir: previsto 4 000 EUR, realizado 4 200 EUR, desvio 200 EUR e margem 3 577,77 EUR.
4. Criar pacote de catarata no Porto e cancelar antes de iniciar.
5. Criar pacote joelho em Lisboa, atribuir médico elegível, aprovar, inserir todos os recursos e concluir: previsto e realizado 4 000 EUR, desvio zero, margem 1 250 EUR.
6. Confirmar ausência de ações de consumo/conclusão nos episódios terminais, bloqueio de campo obrigatório e rejeição de paciente duplicado.

Evidência em browser-acceptance.json e screenshots/aceitacao-*.png.

## Problemas encontrados e corrigidos

- UPDATE de vínculo médico, especialidade médica ou especialidade do procedimento podia invalidar uma equipa já atribuída. Três triggers passam a preservar essas relações.
- A afinidade INTEGER do SQLite aceitava texto e frações em campos monetários. As 17 tabelas foram convertidas para STRICT. Foi criado um backup e todos os registos foram comparados antes de substituir a base.
- O detalhe de episódio importado sem orçamento causava erro não controlado. Passou a apresentar rejeição legível.
- Datas sem hora local ou com segundos/fuso passavam pela validação genérica. O serviço exige agora o formato local de minutos usado pelo formulário.
- Identificadores acima do limite do SQLite podiam interromper o pedido. Passaram a receber resposta 400.

## Limites da verificação

A cobertura corresponde às funcionalidades implementadas e aos cenários descritos. Não é uma prova de ausência de qualquer defeito possível. Não se testou uma impressora física, integração hospitalar, publicação externa nem autenticação, que não existem neste protótipo. O botão de impressão e as regras CSS para impressão estão presentes; a impressão física não é declarada como executada. A conferência humana de completude dos consumos e a revisão do grupo continuam necessárias.
