"""Gera artefactos coerentes com o DDL final; não modifica a base."""
from pathlib import Path
import csv, sqlite3, platform, json, html
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'documentation'

FR=[
('FR01','Selecionar uma unidade','Gestor','Painel, preços, pacotes e episódios refletem a unidade escolhida.'),
('FR02','Consultar e atualizar preços avulsos','Gestor','Atualizar o catálogo da unidade sem alterar orçamentos guardados.'),
('FR03','Consultar pacotes e composição','Gestor','Apresentar recursos, quantidades, custo atual e preço de venda por unidade.'),
('FR04','Cadastrar pacientes fictícios','Administrativo','Guardar nome e código único; permitir pesquisa.'),
('FR05','Cadastrar e vincular médicos','Administrativo','Associar profissional a especialidade e unidade; vincular um profissional existente.'),
('FR06','Criar episódio e orçamento','Administrativo','Guardar paciente, unidade, procedimento, data, modalidade e linhas numa transação.'),
('FR07','Atribuir equipa médica','Gestor','Aceitar apenas médicos da unidade e especialidade, antes de iniciar o episódio.'),
('FR08','Aprovar orçamento','Gestor','Aceitar rascunho com linhas em episódio agendado; fixar valores.'),
('FR09','Registar consumos','Operador','Copiar custo unitário atual para o histórico e registar quantidade e motivo opcional.'),
('FR10','Concluir ou cancelar episódio','Gestor','Concluir em curso com cirurgião e consumo; cancelar apenas agendados.'),
('FR11','Analisar custos e margens','Gestor','Apresentar resumo e detalhe com a mesma política de arredondamento; custos abertos são parciais.'),
('FR12','Pesquisar e imprimir','Gestor','Pesquisar nomes, códigos ou estados e imprimir o detalhe através do navegador.')]
BR=[
('BR01','Cada episódio pertence a uma unidade, um paciente e um procedimento.','FK, NOT NULL e bloqueio da identificação do episódio.'),
('BR02','Associações N:M não aceitam identificadores nulos nem pares repetidos.','NOT NULL, FK e PK composta.'),
('BR03','O preço avulso depende do par unidade/procedimento.','PK composta em unit_procedure_price; consulta parametrizada.'),
('BR04','O pacote escolhido corresponde à unidade e ao procedimento do episódio.','Serviço e trigger budget_package_insert.'),
('BR05','Orçamento avulso não tem pacote; orçamento de pacote identifica o pacote.','CHECK em budget.'),
('BR06','A aprovação exige linhas e episódio agendado; existe no máximo um aprovado por episódio.','Triggers e índice único parcial.'),
('BR07','Orçamento aprovado e as suas linhas são imutáveis.','Triggers de INSERT, UPDATE e DELETE.'),
('BR08','Consumo exige aprovação e episódio agendado ou em curso; a primeira inserção inicia o episódio.','Triggers consumption_allowed e consumption_starts_surgery.'),
('BR09','Consumos não podem ser alterados ou apagados nesta versão.','Triggers, incluindo UPDATE e DELETE.'),
('BR10','Estados terminais não reabrem; agendada passa a em_curso ou cancelada; em_curso passa a concluida.','Triggers surgery_initial, surgery_transition e surgery_start.'),
('BR11','A conclusão exige um consumo e um cirurgião atribuído.','Trigger surgery_finish. A conferência de completude dos consumos é manual.'),
('BR12','Médico atribuído tem a especialidade do procedimento e vínculo à unidade.','Trigger team_eligible, bloqueio de UPDATE dos vínculos/especialidades usados e participações imutáveis.'),
('BR13','Quantidades são positivas, até um milhão e com até três casas; custos são não negativos.','CHECK e validação Decimal na aplicação.'),
('BR14','Arredondar cada linha ao cêntimo, metade para cima, antes de somar.','ROUND de produtos não negativos em ambas as views.'),
('BR15','Atualizações do catálogo não reavaliam preços e custos históricos.','Snapshots em budget, budget_line e consumption.'),
('BR16','Criação de episódio, orçamento e linhas é atómica.','Contexto transacional; rollback confirmado após inserção parcial.')]
TABLES={
'unit':'Unidade operacional fictícia, com código, nome e cidade.',
'specialty':'Especialidade do procedimento e habilitação declarada do médico.',
'doctor':'Profissional com registo fictício único.',
'doctor_specialty':'Habilitações de cada médico; associação N:M.',
'patient':'Paciente/cliente fictício comum às unidades; não representa entidade pagadora distinta.',
'surgical_procedure':'Identidade e especialidade do procedimento.',
'item':'Recurso de custo e unidade de medida; não gere stock.',
'package':'Composição comercial identificada por unidade e procedimento.',
'package_item':'Quantidade prevista de um recurso no pacote.',
'surgery':'Episódio cirúrgico e respetivo estado.',
'surgery_doctor':'Participação do médico e papel no episódio.',
'budget':'Orçamento e preço de venda histórico do episódio.',
'budget_line':'Quantidade e custo unitário previstos, copiados no momento do orçamento.',
'consumption':'Recurso efetivamente registado, com quantidade e custo histórico.',
'procedure_pricing':'Referência académica original de modalidade, origem e âmbito do preço; não é o preço efetivo da unidade.',
'doctor_unit':'Vínculo N:M entre médico e unidade.',
'unit_procedure_price':'Preço de venda avulso atual por unidade e procedimento.'}
FIELDS={'unit_id':'Unidade operacional','specialty_id':'Especialidade','doctor_id':'Profissional','patient_id':'Paciente','procedure_id':'Procedimento','package_id':'Pacote','surgery_id':'Episódio','budget_id':'Orçamento','item_id':'Recurso de custo','consumption_id':'Registo de consumo','name':'Nome ou designação','code':'Código único da unidade','city':'Cidade da unidade','registration':'Código profissional fictício único','fictional_code':'Código fictício único do paciente','category':'Categoria do recurso','unit':'Unidade de medida da quantidade','unit_cost_cents':'Custo unitário histórico ou atual, em cêntimos EUR','sale_price_cents':'Preço de venda em cêntimos EUR','quantity':'Quantidade positiva na unidade do recurso','scheduled_at':'Data/hora local planeada em ISO 8601','status':'Estado do ciclo de vida','version':'Número da versão; revisões aprovadas fora do âmbito','modality':'Origem da composição: pacote ou avulso','role':'Papel do profissional no episódio','reason':'Motivo opcional do consumo ou desvio','recorded_at':'Instante UTC de registo','pricing_model':'Modalidade da referência original: fechado ou estimado','reference_price_cents':'Preço original simulado em cêntimos EUR','price_origin':'Origem do valor de referência','country':'País PT','currency':'Moeda EUR','notes':'Âmbito e notas de nomenclatura/inclusões por confirmar'}


def mdtable(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(str(x).replace('|',' / ').replace('\n',' ') for x in r)+' |\n' for r in rows)


def write(name,content):
    if name in ('validation.md','ai-use-summary.md'):
        content += '\n\n## Verificação alargada\n\nAlém das 32 regressões, passaram 37 testes adicionais de serviços e HTTP: 69 no total. A revisão acrescentou tabelas STRICT, três proteções de alteração de vínculos e especialidade, datas locais com minutos e respostas controladas para episódios sem orçamento ou identificadores fora do intervalo. O ficheiro acceptance-results.json regista a suite adicional. browser-acceptance.json descreve cadastros, preços, avulso, pacote, cancelamento, erros de formulário e ecrã pequeno, todos numa cópia independente. Não foi testada uma impressora física.\n'
    target=D/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding='utf-8')


def main():
    con=sqlite3.connect((ROOT/'data/cirurgias.db').as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    counts={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in TABLES}
    (D/'inventory.json').write_text(json.dumps({'version':'1.0','counts':counts,'views':2,'triggers':con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0],'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'integrity':con.execute('PRAGMA integrity_check').fetchone()[0],'foreign_key_errors':[list(r) for r in con.execute('PRAGMA foreign_key_check')]},indent=2),encoding='utf-8')
    write('requirements.md','# Requisitos funcionais da versão 1.0\n\n'+mdtable(['ID','Requisito','Ator conceptual','Aceitação'],FR)+'\nOs atores descrevem responsabilidades. A aplicação local não implementa autenticação nem permissões por utilizador. Revisão de orçamento aprovado, stock, faturação e integrações são excluídos.\n')
    write('business-rules.md','# Regras de negócio da versão 1.0\n\n'+mdtable(['ID','Regra','Implementação'],BR)+'\nAs políticas de interface validam também o unit_id nos pedidos. A seleção de unidade é contexto operacional, não autorização de segurança. Não se faz gestão de conflitos de agenda.\n')
    write('project-brief.md','''# Cirurgia Controle

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
''')
    write('technical-stack.md',f'''# Tecnologias e arquitetura da versão 1.0

Base: SQLite {sqlite3.sqlite_version}; dialeto SQLite, PRAGMA foreign_keys=ON em cada ligação. Backend: Python {platform.python_version()}, compatível com Python 3.13, biblioteca padrão. HTML, CSS e JavaScript nativo; sem ORM nem dependências externas para executar a aplicação. Arquitetura: navegador → HTTP local → serviços Python → data/cirurgias.db. Servidor ThreadingHTTPServer ligado apenas a 127.0.0.1. Porta padrão 8000; --port permite outra porta e --db uma cópia para demonstração.

O SGBD escolhido para esta entrega é SQLite. Todas as 17 tabelas são STRICT (SQLite 3.37 ou superior), rejeitando texto e frações em campos monetários inteiros. A persistência é a mesma base entregue e reconstruível a partir de seis scripts SQL. Não há fontes ocultas. Inicialização: schema, views, programmable_objects, seed, catalog e demo. Construção primeiro em memória, depois backup SQLite para destino novo. Recusa sobrescrever base existente.

Dinheiro em cêntimos inteiros. Quantidades REAL limitadas a três casas e verificadas com Decimal no serviço. Cada produto de quantidade por custo é arredondado ao cêntimo antes da soma; produtos não negativos usam metade para cima. Ambos os relatórios usam a mesma regra. Esta opção foi testada com meios cêntimos; não é uma implementação de contabilidade fiscal.

Ferramentas documentais de geração: reportlab, pypdfium2, Pillow e @oai/artifact-tool no ambiente de autoria. Não são dependências da aplicação do professor. Segredos e credenciais não são necessários. O servidor local não é uma implantação de produção.
''')
    write('ai-use-summary.md','''# Uso de IA e validação

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
''')
    write('validation.md','''# Verificação da versão 1.0

Em 19/10/2026 foram executados 32 testes de regressão, todos aprovados. Consulte test-results.json. Cada teste trabalha numa cópia temporária reconstruída dos scripts; não modifica data/cirurgias.db. Foram verificados contagens, integridade, FK, snapshots, imutabilidade, transições, elegibilidade médica, unidade, rollback após inserções parciais, quantidades, arredondamento, geração de todas as páginas e escape HTML.

No navegador foi observada a alteração do painel de Coimbra (83 episódios) para Lisboa (80 episódios). Numa cópia separada foram criados episódio e orçamento 244 por pacote, atribuído cirurgião, aprovado o orçamento, registada meia hora de sala e concluída a cirurgia. O consumo real demonstrado foi 200 EUR. Trata-se de um teste de fluxo, não de uma simulação de cirurgia com todos os recursos registados. A base final continua com 243 episódios.

Capturas reais: screenshots/painel.png, detalhe.png, pacotes.png, precos.png e fluxo-concluido.png. O último ficheiro é evidência do teste na cópia, não um registo da base final. Mockups separados representam planeamento da revisão da interface e não imagens históricas anteriores à primeira implementação.

Limitações: contabilidade fiscal, segurança multiutilizador, validação clínica, revisão/estorno de factos e deteção automática de recursos em falta estão fora do âmbito. A conclusão do episódio depende da conferência manual do operador. As provas técnicas não significam validação humana da revisão mais recente.
''')
    # Exact column-level dictionary, including all foreign keys and composite uniqueness.
    with (D/'data-dictionary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['Table','Attribute','Data Type','PK','FK','Nullable','Unique','Allowed Values / Domain','Description','Example'])
        for t,description in TABLES.items():
            columns=con.execute(f'PRAGMA table_info({t})').fetchall();pkcols=[r['name'] for r in columns if r['pk']]
            fk={r['from']:r['table']+'.'+r['to'] for r in con.execute(f'PRAGMA foreign_key_list({t})')}
            constraints=[]
            for idx in con.execute(f'PRAGMA index_list({t})').fetchall():
                if idx['unique']:constraints.append(('partial: ' if idx['partial'] else '')+','.join(r['name'] for r in con.execute(f'PRAGMA index_info("{idx["name"]}")')))
            for col in columns:
                n=col['name'];nullable=not(col['notnull'] or (col['pk'] and len(pkcols)==1 and col['type']=='INTEGER'))
                domain=''
                if n.endswith('_cents'):domain='>=0, cêntimos EUR; preço avulso >0'
                if n=='quantity':domain='0<q<=1000000; até 3 casas decimais'
                if n=='status':domain='agendada,em_curso,concluida,cancelada' if t=='surgery' else 'rascunho,aprovado,substituido (reservado)'
                if n=='modality':domain='avulso,pacote'
                if n=='category':domain='equipa,sala,material,medicamento,protese'
                example=con.execute(f'SELECT "{n}" FROM "{t}" WHERE "{n}" IS NOT NULL LIMIT 1').fetchone()
                w.writerow([t,n,col['type'],'Y' if col['pk'] else '',fk.get(n,''),'Y' if nullable else 'N','; '.join(x for x in constraints if n in x.replace('partial: ','').split(',')),domain,description+' '+FIELDS.get(n,n),example[0] if example else ''])
    links=[]
    for t in TABLES:
        for fk in con.execute(f'PRAGMA foreign_key_list({t})'):
            col=next(r for r in con.execute(f'PRAGMA table_info({t})') if r['name']==fk['from'])
            # procedure_pricing PK and optional package reference have distinct cardinalities.
            right='o|' if t=='procedure_pricing' else 'o{'
            left='||' if col['notnull'] or (t=='procedure_pricing') else 'o|'
            links.append(f' {fk["table"]} {left}--{right} {t} : {fk["from"]}')
    erd='# ERD da versão 1.0\n\n```mermaid\nerDiagram\n'+'\n'.join(links)+'\n'
    for t in TABLES:
        erd+=' '+t+' {\n'
        for col in con.execute(f'PRAGMA table_info({t})'):
            isfk=any(r['from']==col['name'] for r in con.execute(f'PRAGMA foreign_key_list({t})'))
            erd+=f'  {col["type"]} {col["name"]}'+(' PK,FK' if col['pk'] and isfk else ' PK' if col['pk'] else ' FK' if isfk else '')+'\n'
        erd+=' }\n'
    erd+='```\n\nCardinalidades referem-se à estrutura. Aprovação exige linhas, e conclusão exige cirurgião e consumo, por triggers. Um episódio pode ter zero orçamentos no DDL; o serviço cria sempre um orçamento atomicamente. package_id em budget é opcional apenas na modalidade avulso. Quantidades e snapshots pertencem à associação/operação, não ao catálogo.\n'
    write('diagrams/ERD.md',erd)
    write('normalisation.md','''# Normalização

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
''')
    con.close()
    print('Documentação, inventário, ERD e dicionário gerados.')


if __name__=='__main__':main()
