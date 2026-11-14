# Verificação da versão 1.0

Em 19/10/2026 foram executados 32 testes de regressão, todos aprovados. Consulte test-results.json. Cada teste trabalha numa cópia temporária reconstruída dos scripts; não modifica data/cirurgias.db. Foram verificados contagens, integridade, FK, snapshots, imutabilidade, transições, elegibilidade médica, unidade, rollback após inserções parciais, quantidades, arredondamento, geração de todas as páginas e escape HTML.

No navegador foi observada a alteração do painel de Coimbra (83 episódios) para Lisboa (80 episódios). Numa cópia separada foram criados episódio e orçamento 244 por pacote, atribuído cirurgião, aprovado o orçamento, registada meia hora de sala e concluída a cirurgia. O consumo real demonstrado foi 200 EUR. Trata-se de um teste de fluxo, não de uma simulação de cirurgia com todos os recursos registados. A base final continua com 243 episódios.

Capturas reais: screenshots/painel.png, detalhe.png, pacotes.png, precos.png e fluxo-concluido.png. O último ficheiro é evidência do teste na cópia, não um registo da base final. Mockups separados representam planeamento da revisão da interface e não imagens históricas anteriores à primeira implementação.

Limitações: contabilidade fiscal, segurança multiutilizador, validação clínica, revisão/estorno de factos e deteção automática de recursos em falta estão fora do âmbito. A conclusão do episódio depende da conferência manual do operador. As provas técnicas não significam validação humana da revisão mais recente.


## Verificação alargada

Além das 32 regressões, passaram 37 testes adicionais de serviços e HTTP: 69 no total. A revisão acrescentou tabelas STRICT, três proteções de alteração de vínculos e especialidade, datas locais com minutos e respostas controladas para episódios sem orçamento ou identificadores fora do intervalo. O ficheiro acceptance-results.json regista a suite adicional. browser-acceptance.json descreve cadastros, preços, avulso, pacote, cancelamento, erros de formulário e ecrã pequeno, todos numa cópia independente. Não foi testada uma impressora física.
