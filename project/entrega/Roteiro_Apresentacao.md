# Roteiro de apresentação

Objetivo: cerca de 10 minutos de apresentação e demonstração, mais 5 minutos de perguntas.

| Slides | Tempo aproximado | Mensagem |
|---|---|---|
| 1 e 2 | 1 min | Problema, domínio e diferença entre preço de venda e custo |
| 3 e 4 | 1 min 30 | Fluxo, entidades e associações N:M |
| 5 e 6 | 1 min 20 | Exemplo económico, unidades e catálogos |
| 7 e 8 | 1 min | Evidência real do protótipo |
| 9 e 10 | 1 min 30 | Integridade, transações e testes |
| 11 | 40 s | Correções de IA e validação |
| 12 e demo | 3 min | Executar fluxo e explicar limites |

## Preparação

Execute iniciar.bat e abra o endereço indicado. Leia README.md. Para ensaiar sem alterar a base entregue, copie data/cirurgias.db para uma pasta de ensaio e use `py -3.13 application/app.py --db caminho/copia.db --port 8001`. Mantenha a cópia de entrega intacta. As notas dos slides contêm indicações por diapositivo.

## Demonstração

1. No painel, mudar Coimbra para Lisboa: 83 e 80 episódios, respetivamente, na demonstração original.
2. Mostrar Preços avulsos, pesquisar catarata e distinguir do pacote com composição. Os montantes são fictícios.
3. Voltar a Coimbra e abrir o episódio 1: previstos 4 000 EUR, reais 4 350 EUR, desvio 350 EUR (+8,75%) e margem final 650 EUR.
4. Em Orçamentos, selecionar Maria Silva, Artroplastia total do joelho, data, Pacote e pacote joelho padrão. Criar o rascunho.
5. Atribuir Ana Martins como cirurgião e aprovar. Explicar a transação de criação e os snapshots.
6. Registar os consumos. Para uma demonstração completa do exemplo padrão: equipa ortopédica 1, sala 2 horas, materiais ortopédicos 1 e prótese de joelho 1. O custo final será 4 000 EUR. Se o tempo só permitir meia hora de sala, explicar expressamente que se trata de teste funcional, com recursos incompletos.
7. Concluir e mostrar que o estado é terminal. A conferência de completude é manual nesta versão.

## Perguntas para ensaiar

- Por que uma tabela por unidade seria pior? Identidades seriam duplicadas; usamos FK e associações.
- Onde estão as N:M? Médico/especialidade, médico/unidade, médico/cirurgia e pacote/recurso.
- Por que guardar custo histórico não viola a 3FN? É um facto da operação, diferente do custo atual do recurso.
- O que acontece se falhar a segunda linha do orçamento? A transação reverte episódio, orçamento e linhas.
- Como se impede usar pacote de outra unidade? Verificação no serviço e trigger cruzando pacote e episódio.
- O que acontece ao atualizar o preço? Só propostas futuras usam o novo preço; snapshots permanecem iguais.
- Como se arredonda? Cada linha positiva é arredondada ao cêntimo antes de somar, tanto no detalhe como no resumo.
- O seletor é uma permissão? Não; o protótipo é local e não autentica utilizadores.
- O que falta para produção? Segurança, preços temporais, estornos, auditoria, concorrência, rastreabilidade e validação do domínio real.

## Conferência do grupo

Confirmar tema com o professor, preencher a identificação dos autores conforme o portal e rever as decisões novas. Os testes técnicos executados pela IA não substituem a capacidade de explicar e corrigir a solução na defesa.
