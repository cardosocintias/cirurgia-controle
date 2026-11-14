# Normalização

## Primeira forma normal
Cada atributo contém um valor do domínio. Médicos, especialidades, recursos e unidades não são listas dentro de uma célula. As relações N:M são linhas em doctor_specialty, doctor_unit, surgery_doctor e package_item. A interface pode agregar nomes para leitura; isso não altera a estrutura armazenada.

## Segunda forma normal
Nas entidades com chave simples, todos os atributos dependem do identificador. Nas associações, a quantidade de package_item depende do par pacote/artigo; em budget_line quantidade e custo histórico dependem do par orçamento/artigo; em surgery_doctor o papel depende do par cirurgia/médico; em unit_procedure_price o preço depende do par unidade/procedimento. Não guardar nome de médico em doctor_unit, nem nome de unidade na tabela de preços, evita dependências parciais.

## Terceira forma normal
unit_id determina código, nome e cidade; doctor_id determina nome e registo; patient_id determina nome e código; procedure_id determina nome e specialty_id. O nome da especialidade pertence apenas a specialty. surgery_id determina unidade, paciente, procedimento, data e estado. budget_id determina episódio, versão, modalidade, pacote e preço histórico. consumption_id determina episódio, recurso, quantidade, custo histórico, motivo e instante. Não se guardam totais de orçamento ou desvio: são derivados nas views.

## Factos históricos e dependências
item_id determina o custo atual em item, mas não determina o custo histórico de uma linha passada. O custo guardado no orçamento depende do orçamento/artigo e do instante da decisão. Copiá-lo preserva um facto distinto, sem violar a 3FN. De modo semelhante, unit_procedure_price guarda preço atual por unidade/procedimento, enquanto budget guarda o preço efetivamente proposto. A referência original procedure_pricing contém a origem/âmbito académico; o preço específico da unidade é outro facto. Esta separação não implementa um catálogo temporal de vigências.

## Limites semânticos
A 3FN não garante uma transição de estado, nem impede combinar um pacote de outra unidade: essas dependências de negócio são verificadas por triggers e serviço. O relatório e o dicionário distinguem integridade estrutural de regras de ciclo de vida. Não foi feita desnormalização para desempenho; índices e views bastam para a dimensão de demonstração.
