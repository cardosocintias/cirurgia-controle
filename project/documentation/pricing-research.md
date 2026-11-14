# Pesquisa e política de preços do catálogo

Consulta de fontes públicas em 17 de outubro de 2026. País: Portugal. Moeda: EUR. Objeto pretendido: preço particular cobrado ao paciente, distinto do custo interno do hospital.

## Decisão para esta iteração

Não foi encontrada nesta pesquisa uma amostra homogénea de preços particulares completos para os 56 procedimentos. Por isso, não se calculou nem se afirma uma média de mercado. A coluna de referência é uma escolha fictícia para simular o sistema, sem fórmula de extrapolação de tarifas convencionadas e sem atualização por inflação.

O ficheiro procedure-catalog.md apresenta os valores por procedimento. A base guarda a modalidade, a origem simulada/por definir e as notas sobre inclusões. O preço de catálogo não altera automaticamente pacotes, custos unitários, orçamentos aprovados ou consumos históricos. Não há passagem automática do preço de venda para o custo hospitalar.

## Fontes encontradas e limites

1. [Tabela particular CHSF disponibilizada pela APIR](https://www.apir.org.pt/wp-content/uploads/2022/04/Tabela-CHSF-protocolos.pdf), secção de cirurgias, páginas 6–7. Tem valores por intervenção, mas exclui honorários médicos e avisa que os preços podem mudar. Não fornece um preço completo atual por episódio. Exemplo: gastrectomia parcial/subtotal, 4 000 €, sem honorários. Não se usou esse valor como preço total de gastrectomia nem como média nacional. A data de vigência não foi confirmada; o caminho do ficheiro não prova a sua atualidade. Algumas descrições apresentam ambiguidades, pelo que não foram importadas como nomenclatura clínica validada.

2. [Pacotes de cirurgia estética AMI 2025](https://ami.org.pt/wp-content/uploads/2025/02/TABELA-DE-PACOTES-DE-CIRURGIA-ESTETICA-2025.pdf), página 1. Publica referências por pacote e extensão. Inclui honorários e determinados serviços hospitalares, mas exclui próteses e exames, entre outras despesas. Refere valores convencionados por unidade. Não é uma média do mercado particular nem demonstra que todos os particulares tenham acesso a esses valores. Não se copiaram esses preços para os valores fictícios do catálogo.

3. [Artroplastia do joelho — Saúde e Bem Estar](https://www.saudebemestar.pt/pt/clinica/ortopedia/artroplastia-de-joelho/). Não publica um montante fixo; indica dependência do tipo de prótese, procedimento e regime de pagamento. Suporta a necessidade de definir o âmbito, sem fornecer uma média utilizável.

4. [Tabela de preços e regras da rede ADSE](https://www2.adse.pt/sou-beneficiario/rede-adse/tabela-de-precos-e-regras/). Define encargos convencionados entre a ADSE, beneficiários e prestadores. Não foi tratada como tabela particular nem como custo hospitalar.

## Preços fechados definidos pelo aluno

Cirurgia de catarata; septoplastia; microcirurgia endonasal; reconstrução do ligamento cruzado; histerectomia; vasectomia; circuncisão; cirurgia de hidrocele; colecistectomia; hemorroidectomia; abdominoplastia; lipoaspiração.

A modalidade é uma regra da instituição fictícia e não uma afirmação sobre todos os prestadores portugueses. A pedido do aluno, todos os montantes anteriormente pendentes receberam valores fictícios, incluindo os 12 preços fechados. Exemplos: catarata 2 000 €, septoplastia 3 000 €, vasectomia 900 € e colecistectomia 4 500 €. São escolhas de simulação sem cálculo de média das fontes. As inclusões ainda precisam de validação: honorários, anestesia, sala, consumíveis, implantes, internamento e exclusões. Uma alteração do custo real não altera automaticamente o preço fechado.

## Nomenclatura e unidades

Vasectomia foi deduplicada. Anca, joelho e ombro; mamoplastia de aumento e redutora; hérnia discal cervical e lombar foram separados. Hallux vago foi normalizado para correção de hallux valgus; síndrome do túnel cárpico foi representada pelo procedimento de libertação.

Três entradas mantêm a designação pendente de confirmação, agora com valor fictício: injeção de substituto vítreo/pneumopexia; histerosplastia; extirpação de hérnia. Não se presume que injeção de medicamento intraocular e pneumopexia sejam o mesmo ato. Foraminectomia foi preservada, com nota para confirmar se se pretende foraminotomia. Aneurisma, descolamento de retina e hérnia incisional foram descritos como tratamentos cirúrgicos, mantendo técnicas por definir.

Os preços oftalmológicos foram definidos por olho quando indicado; não devem ser comparados com preços bilaterais. Outros procedimentos também explicitam hipóteses de lateralidade. As propostas de âmbito são simplificações de dados a validar pelo grupo.
