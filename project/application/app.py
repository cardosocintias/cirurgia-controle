"""Cirurgia Controle 1.0. Servidor local e serviços transacionais, dados fictícios."""
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit, urlencode
import argparse
import html
import sqlite3
import json

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/cirurgias.db'


class Connection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def connect():
    con = sqlite3.connect(DB, factory=Connection, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def initialize():
    if DB.exists():
        raise ValueError('Base existente preservada. Não execute --init novamente.')
    DB.parent.mkdir(parents=True, exist_ok=True)
    # Construir em memória antes de criar qualquer ficheiro de demonstração.
    from contextlib import closing
    with closing(sqlite3.connect(':memory:')) as temporary:
        for name in ('schema', 'views', 'programmable_objects', 'seed', 'catalog', 'demo'):
            temporary.executescript((ROOT / f'data/{name}.sql').read_text(encoding='utf-8'))
        temporary.commit()
        with connect() as con:
            temporary.backup(con)


def text(value, maximum=120):
    value = str(value).strip()
    if not value or len(value) > maximum:
        raise ValueError(f'Preencha o texto com 1 a {maximum} caracteres.')
    return value


def quantity(value):
    try:
        number = Decimal(str(value).replace(',', '.'))
        if not number.is_finite() or number <= 0 or number > 1000000 or number * 1000 != (number * 1000).to_integral_value():
            raise ValueError('Quantidade: positiva, até 1 000 000 e no máximo 3 casas decimais.')
        return float(number)
    except InvalidOperation:
        raise ValueError('Quantidade inválida.') from None


def cents(value):
    try:
        number = Decimal(str(value).replace(',', '.'))
        if not number.is_finite() or number < 0 or number > 10000000 or number * 100 != (number * 100).to_integral_value():
            raise ValueError('Valor monetário inválido; utilize até duas casas decimais.')
        return int(number * 100)
    except InvalidOperation:
        raise ValueError('Valor monetário inválido.') from None


def require_unit(con, unit_id):
    if not con.execute('SELECT 1 FROM unit WHERE unit_id=?', (unit_id,)).fetchone():
        raise ValueError('Unidade inexistente.')


def require_surgery(con, surgery_id, unit_id):
    row = con.execute('SELECT * FROM surgery WHERE surgery_id=? AND unit_id=?', (surgery_id, unit_id)).fetchone()
    if not row:
        raise ValueError('Episódio não pertence à unidade selecionada.')
    return row


def create_surgery(unit_id, patient_id, procedure_id, scheduled_at, modality, package_id=None, lines=None):
    parsed = datetime.fromisoformat(scheduled_at)
    if parsed.tzinfo is not None or parsed.isoformat(timespec='minutes') != scheduled_at:
        raise ValueError('Data/hora local inválida. Utilize AAAA-MM-DDTHH:MM, sem fuso ou segundos.')
    if modality not in ('pacote', 'avulso'):
        raise ValueError('Modalidade inválida.')
    with connect() as con:
        require_unit(con, unit_id)
        price = con.execute('SELECT sale_price_cents FROM unit_procedure_price WHERE unit_id=? AND procedure_id=?', (unit_id, procedure_id)).fetchone()
        if not price:
            raise ValueError('Procedimento sem preço nesta unidade.')
        if modality == 'pacote':
            package = con.execute('SELECT * FROM package WHERE package_id=? AND unit_id=? AND procedure_id=?', (package_id, unit_id, procedure_id)).fetchone()
            if not package:
                raise ValueError('Pacote incompatível com a unidade ou procedimento.')
            price = package
            lines = [(r['item_id'], r['quantity']) for r in con.execute('SELECT * FROM package_item WHERE package_id=?', (package_id,))]
        else:
            package_id = None
        if not lines:
            raise ValueError('O orçamento exige pelo menos um componente de custo.')
        surgery_id = con.execute("INSERT INTO surgery(unit_id,patient_id,procedure_id,scheduled_at,status) VALUES(?,?,?,?,'agendada')", (unit_id, patient_id, procedure_id, scheduled_at)).lastrowid
        budget_id = con.execute("INSERT INTO budget(surgery_id,version,status,sale_price_cents,modality,package_id) VALUES(?,1,'rascunho',?,?,?)", (surgery_id, price['sale_price_cents'], modality, package_id)).lastrowid
        for item_id, amount in lines:
            cost = con.execute('SELECT unit_cost_cents FROM item WHERE item_id=?', (item_id,)).fetchone()
            if not cost:
                raise ValueError('Componente inexistente. A operação foi revertida.')
            con.execute('INSERT INTO budget_line VALUES(?,?,?,?)', (budget_id, item_id, quantity(amount), cost[0]))
        return surgery_id


def approve_budget(unit_id, budget_id):
    with connect() as con:
        row = con.execute('SELECT surgery_id FROM budget WHERE budget_id=?', (budget_id,)).fetchone()
        if not row:
            raise ValueError('Orçamento inexistente.')
        require_surgery(con, row[0], unit_id)
        changed = con.execute("UPDATE budget SET status='aprovado' WHERE budget_id=? AND status='rascunho'", (budget_id,)).rowcount
        if changed != 1:
            raise ValueError('O orçamento já não está em rascunho.')


def record_consumption(unit_id, surgery_id, item_id, amount, reason=''):
    amount = quantity(amount)
    with connect() as con:
        require_surgery(con, surgery_id, unit_id)
        item = con.execute('SELECT unit_cost_cents FROM item WHERE item_id=?', (item_id,)).fetchone()
        if not item:
            raise ValueError('Componente inexistente.')
        if len(reason) > 500:
            raise ValueError('Motivo demasiado longo.')
        con.execute('INSERT INTO consumption(surgery_id,item_id,quantity,unit_cost_cents,reason) VALUES(?,?,?,?,?)', (surgery_id, item_id, amount, item[0], reason.strip() or None))


def change_state(unit_id, surgery_id, status):
    with connect() as con:
        require_surgery(con, surgery_id, unit_id)
        con.execute('UPDATE surgery SET status=? WHERE surgery_id=?', (status, surgery_id))


def assign_doctor(unit_id, surgery_id, doctor_id, role):
    if role not in ('cirurgiao', 'assistente', 'anestesista'):
        raise ValueError('Papel inválido.')
    with connect() as con:
        require_surgery(con, surgery_id, unit_id)
        con.execute('INSERT INTO surgery_doctor VALUES(?,?,?)', (surgery_id, doctor_id, role))


def esc(value):
    return html.escape(str(value), quote=True)


def money(value):
    return '—' if value is None else f'{value / 100:,.2f} €'.replace(',', ' ').replace('.', ',')


def select(name, rows, key, label, empty=False):
    opts = '<option value="">Selecionar</option>' if empty else ''
    opts += ''.join(f'<option value="{esc(r[key])}">{esc(r[label])}</option>' for r in rows)
    return f'<select name="{name}" required>{opts}</select>'


def table(headers, rows):
    body = ''.join('<tr>' + ''.join(f'<td>{v}</td>' for v in row) + '</tr>' for row in rows)
    return '<div class="table-scroll"><table><thead><tr>' + ''.join(f'<th>{esc(h)}</th>' for h in headers) + '</tr></thead><tbody>' + (body or f'<tr><td colspan="{len(headers)}">Sem registos para este filtro.</td></tr>') + '</tbody></table></div>'


def form(action, unit_id, fields, button, back='orcamentos'):
    return f'<form method="post" action="/{action}"><input type="hidden" name="unit_id" value="{unit_id}"><input type="hidden" name="back" value="{back}">{fields}<button>{esc(button)}</button></form>'


def label(title, field):
    return f'<label>{esc(title)}{field}</label>'


def input_field(name, kind='text', **attrs):
    return f'<input name="{name}" type="{kind}" required ' + ' '.join(f'{k}="{esc(v)}"' for k, v in attrs.items()) + '>'


def render(path='/', unit_id=1, q='', message='', detail_id=None):
    with connect() as con:
        require_unit(con, unit_id)
        units = con.execute('SELECT * FROM unit').fetchall()
        unit = next(r for r in units if r['unit_id'] == unit_id)
        summary = con.execute('SELECT * FROM v_surgery_financial WHERE unit_id=? ORDER BY scheduled_at DESC', (unit_id,)).fetchall()
        patients = con.execute('SELECT * FROM patient ORDER BY name').fetchall()
        procedures = con.execute('SELECT p.*,pp.sale_price_cents,e.name specialty FROM surgical_procedure p JOIN unit_procedure_price pp USING(procedure_id) JOIN specialty e USING(specialty_id) WHERE pp.unit_id=? ORDER BY e.name,p.name', (unit_id,)).fetchall()
        packages = con.execute('SELECT k.*,p.name procedure_name FROM package k JOIN surgical_procedure p USING(procedure_id) WHERE k.unit_id=? ORDER BY k.name', (unit_id,)).fetchall()
        items = con.execute('SELECT * FROM item ORDER BY name').fetchall()
        doctors = con.execute('SELECT d.* FROM doctor d JOIN doctor_unit du USING(doctor_id) WHERE du.unit_id=? ORDER BY d.name', (unit_id,)).fetchall()
        filtered = [r for r in summary if q.casefold() in (r['patient_name'] + ' ' + r['procedure_name'] + ' ' + r['status'] + ' ' + str(r['surgery_id'])).casefold()]
        content = ''
        titles = {'/': ('Painel de gestão', 'Uma visão económica dos episódios da unidade.'), '/procedimentos': ('Procedimentos avulsos', 'Preços de venda por unidade, separados dos custos internos.'), '/pacotes': ('Pacotes cirúrgicos', 'Composição prevista e preço de venda de cada pacote.'), '/medicos': ('Equipa médica', 'Profissionais vinculados à unidade e respetivas especialidades.'), '/pacientes': ('Pacientes', 'Cadastro comum às unidades. Utilize apenas dados fictícios.'), '/orcamentos': ('Orçamentos e episódios', 'Preparar, aprovar e acompanhar cada cirurgia.'), '/detalhe': ('Detalhe do episódio', 'Previsão, realização e equipa médica.')}
        if path not in titles:
            raise LookupError('Página inexistente.')
        title, subtitle = titles[path]
        if path == '/':
            done = [r for r in summary if r['status'] == 'concluida']
            actual = sum(r['actual_cents'] for r in done)
            deviation = sum(r['variance_cents'] or 0 for r in done)
            cards = [(len(summary), 'Episódios na unidade'), (sum(r['status'] in ('agendada', 'em_curso') for r in summary), 'Episódios abertos'), (money(actual), 'Custo realizado · concluídos'), (money(deviation), 'Desvio · concluídos')]
            content = '<div class="metrics">' + ''.join(f'<article><span>{esc(t)}</span><strong>{v}</strong></article>' for v,t in cards) + '</div>'
            counts = [(state, sum(r['status'] == state for r in summary)) for state in ('agendada','em_curso','concluida','cancelada')]
            content += '<div class="split"><section><h2>Distribuição dos episódios</h2>' + ''.join(f'<div class="bar-row"><span>{s}</span><div><i style="width:{max(2, n/max(1,len(summary))*100)}%"></i></div><b>{n}</b></div>' for s,n in counts) + '</section><section><h2>Fluxo de trabalho</h2><ol><li>Preparar orçamento avulso ou a partir de pacote.</li><li>Atribuir o cirurgião e aprovar o orçamento.</li><li>Registar recursos utilizados.</li><li>Concluir e analisar custos e margem.</li></ol><a class="button" href="/orcamentos?unit_id='+str(unit_id)+'">Novo orçamento →</a></section></div>'
            content += '<section><h2>Episódios recentes</h2>' + episode_table(summary[:10], unit_id) + '</section>'
        elif path == '/procedimentos':
            data = [r for r in procedures if q.casefold() in (r['name']+' '+r['specialty']).casefold()]
            content = '<section>' + search(path,unit_id,q) + table(['ID','Especialidade','Procedimento','Preço avulso'],[(r['procedure_id'],esc(r['specialty']),esc(r['name']),money(r['sale_price_cents'])) for r in data]) + '</section>'
            fields = label('Procedimento',select('procedure_id',procedures,'procedure_id','name')) + label('Novo preço de venda (€)',input_field('price','number',min='0.01',step='0.01'))
            content += '<section><h2>Atualizar preço da unidade</h2><p>O novo valor aplica-se a orçamentos futuros. Os valores já guardados permanecem iguais.</p>' + form('price',unit_id,fields,'Guardar preço','procedimentos') + '</section>'
        elif path == '/pacotes':
            rows=[]
            for r in packages:
                comp=con.execute('SELECT i.name,i.unit,pi.quantity FROM package_item pi JOIN item i USING(item_id) WHERE package_id=?',(r['package_id'],)).fetchall()
                cost=con.execute('SELECT SUM(ROUND(pi.quantity*i.unit_cost_cents)) FROM package_item pi JOIN item i USING(item_id) WHERE package_id=?',(r['package_id'],)).fetchone()[0]
                if q.casefold() in (r['name']+' '+r['procedure_name']).casefold():
                    rows.append((esc(r['name']),esc(r['procedure_name']),'<br>'.join(f'{esc(i["name"])} · {i["quantity"]:g} {esc(i["unit"])}' for i in comp),money(cost),money(r['sale_price_cents'])))
            content='<section>'+search(path,unit_id,q)+table(['Pacote','Procedimento','Composição de custos','Custo atual','Preço de venda'],rows)+'</section>'
        elif path == '/pacientes':
            data=[r for r in patients if q.casefold() in (r['name']+' '+r['fictional_code']).casefold()]
            content='<section>'+search(path,unit_id,q)+table(['Código','Nome'],[(esc(r['fictional_code']),esc(r['name'])) for r in data])+'</section>'
            fields=label('Nome fictício',input_field('name',maxlength=120))+label('Código fictício único',input_field('code',maxlength=40))
            content+='<section><h2>Novo paciente</h2>'+form('patient',unit_id,fields,'Guardar paciente','pacientes')+'</section>'
        elif path == '/medicos':
            specialties=con.execute('SELECT * FROM specialty ORDER BY name').fetchall()
            rows=[]
            for d in doctors:
                sp=', '.join(r[0] for r in con.execute('SELECT name FROM specialty JOIN doctor_specialty USING(specialty_id) WHERE doctor_id=?',(d['doctor_id'],)))
                if q.casefold() in (d['name']+' '+d['registration']+' '+sp).casefold():rows.append((esc(d['name']),esc(d['registration']),esc(sp)))
            content='<section>'+search(path,unit_id,q)+table(['Nome','Registo fictício','Especialidades'],rows)+'</section>'
            fields=label('Nome fictício',input_field('name',maxlength=120))+label('Registo único',input_field('registration',maxlength=40))+label('Especialidade',select('specialty_id',specialties,'specialty_id','name'))
            content+='<section><h2>Novo médico nesta unidade</h2>'+form('doctor',unit_id,fields,'Guardar médico','medicos')+'</section>'
            fields=label('Médico existente',select('doctor_id',con.execute('SELECT * FROM doctor ORDER BY name').fetchall(),'doctor_id','name'))
            content+='<section><h2>Vincular médico existente à unidade</h2>'+form('doctor-link',unit_id,fields,'Vincular','medicos')+'</section>'
        elif path == '/orcamentos':
            content='<section><h2>Episódios da unidade</h2>'+search(path,unit_id,q)+'<div class="episode-list">'+episode_table(filtered,unit_id)+'</div></section>'
            fields=label('Paciente',select('patient_id',patients,'patient_id','name'))+label('Procedimento',select('procedure_id',procedures,'procedure_id','name'))+label('Data e hora',input_field('scheduled_at','datetime-local'))
            fields+='<label>Modalidade<select name="modality" id="modality"><option value="pacote">Pacote</option><option value="avulso">Avulso</option></select></label><p class="hint">Existem pacotes de joelho, hérnia e catarata. Para os restantes procedimentos, escolha Avulso e indique os recursos previstos.</p><div id="package-fields">'+label('Pacote compatível',select('package_id',packages,'package_id','name'))+'</div>'
            fields+='<div id="line-fields" hidden><p>Composição do orçamento avulso: indique a quantidade de cada recurso. Zero exclui a linha. O preço de venda vem do catálogo da unidade.</p>'
            fields+=''.join(label(f'{r["name"]} · {money(r["unit_cost_cents"])} / {r["unit"]}',f'<input type="number" name="qty_{r["item_id"]}" value="0" min="0" max="1000000" step="0.001">') for r in items)+'</div>'
            content+='<section><h2>Preparar novo orçamento</h2>'+form('create',unit_id,fields,'Criar episódio e rascunho')+'</section>'
            mapping={str(p['package_id']):p['procedure_id'] for p in packages}
            content+='<script>const map='+json.dumps(mapping)+';const mod=document.getElementById("modality");const ps=document.querySelector("select[name=package_id]");const pr=document.querySelector("select[name=procedure_id]");function refresh(){const av=mod.value==="avulso";document.getElementById("package-fields").hidden=av;ps.disabled=av;document.getElementById("line-fields").hidden=!av;let first=null;for(const o of ps.options){o.hidden=String(map[o.value])!==pr.value;o.disabled=o.hidden;if(!o.hidden&&!first)first=o;}if(first&&(!ps.selectedOptions.length||ps.selectedOptions[0].disabled))ps.value=first.value;if(!first)ps.selectedIndex=-1;}mod.onchange=refresh;pr.onchange=refresh;refresh();</script>'
        elif path == '/detalhe':
            surgery=require_surgery(con,detail_id,unit_id)
            b=con.execute('SELECT * FROM budget WHERE surgery_id=? ORDER BY version DESC LIMIT 1',(detail_id,)).fetchone()
            if b is None:
                raise ValueError('Este episódio não tem orçamento. Reveja a importação dos dados.')
            financial=con.execute('SELECT * FROM v_surgery_financial WHERE surgery_id=?',(detail_id,)).fetchone()
            content=f'<section><div class="section-head"><div><h2>Episódio #{detail_id} · {esc(financial["patient_name"])}</h2><p>{esc(financial["procedure_name"])} · {esc(surgery["scheduled_at"])} · <span class="badge">{esc(surgery["status"])}</span></p></div><button onclick="window.print()">Imprimir</button></div><p>Orçamento #{b["budget_id"]} · {esc(b["modality"])} · {esc(b["status"])} · preço de venda: <b>{money(b["sale_price_cents"])}</b></p>'
            content+=table(['Custo previsto','Custo realizado','Desvio','Margem atual'],[(money(financial['planned_cents']),money(financial['actual_cents']),money(financial['variance_cents']),money(financial['actual_margin_cents']))])
            if surgery['status']!='concluida':content+='<p class="hint">Custos e margem de episódios abertos são parciais. Rascunhos não constituem previsão aprovada.</p>'
            content+='</section>'
            detail=con.execute('SELECT * FROM v_cost_variance WHERE surgery_id=?',(detail_id,)).fetchall()
            content+='<section><h2>Comparação por recurso</h2>'+table(['Recurso','Qtd. prevista','Qtd. real','Previsto','Real'],[(esc(r['item_name']),r['planned_quantity'],r['actual_quantity'],money(r['planned_cents']),money(r['actual_cents'])) for r in detail])+'</section>'
            draft=con.execute('SELECT bl.*,i.name FROM budget_line bl JOIN item i USING(item_id) WHERE budget_id=?',(b['budget_id'],)).fetchall()
            content+='<section><h2>Composição guardada no orçamento</h2>'+table(['Componente','Quantidade','Custo unitário histórico','Total'],[(esc(r['name']),r['quantity'],money(r['unit_cost_cents']),money(con.execute('SELECT CAST(ROUND(?*?) AS INTEGER)',(r['quantity'],r['unit_cost_cents'])).fetchone()[0])) for r in draft])+'</section>'
            team=con.execute('SELECT d.name,sd.role FROM surgery_doctor sd JOIN doctor d USING(doctor_id) WHERE surgery_id=?',(detail_id,)).fetchall()
            content+='<section><h2>Equipa atribuída</h2>'+table(['Médico','Papel'],[(esc(r['name']),esc(r['role'])) for r in team])+'</section>'
            hidden=f'<input type="hidden" name="surgery_id" value="{detail_id}">'
            if surgery['status']=='agendada':
                eligible=con.execute('SELECT d.* FROM doctor d JOIN doctor_unit du USING(doctor_id) JOIN doctor_specialty ds USING(doctor_id) JOIN surgical_procedure p ON p.specialty_id=ds.specialty_id WHERE du.unit_id=? AND p.procedure_id=? AND NOT EXISTS(SELECT 1 FROM surgery_doctor sd WHERE sd.surgery_id=? AND sd.doctor_id=d.doctor_id)',(unit_id,surgery['procedure_id'],detail_id)).fetchall()
                if eligible:
                    fields=hidden+label('Médico elegível',select('doctor_id',eligible,'doctor_id','name'))+'<label>Papel<select name="role"><option value="cirurgiao">Cirurgião</option><option value="assistente">Assistente</option><option value="anestesista">Anestesista</option></select></label>'
                    content+='<section><h2>Atribuir médico</h2>'+form('assign',unit_id,fields,'Atribuir','detalhe')+'</section>'
                if b['status']=='rascunho':content+='<section><h2>Aprovar orçamento</h2>'+form('approve',unit_id,hidden+f'<input type="hidden" name="budget_id" value="{b["budget_id"]}">','Aprovar e fixar valores','detalhe')+'</section>'
            if surgery['status'] in ('agendada','em_curso') and b['status']=='aprovado':
                fields=hidden+label('Recurso',select('item_id',items,'item_id','name'))+label('Quantidade',input_field('quantity','number',min='0.001',max='1000000',step='0.001'))+'<label>Motivo (opcional)<input name="reason" maxlength="500"></label>'
                content+='<section><h2>Registar consumo</h2>'+form('consume',unit_id,fields,'Guardar consumo','detalhe')+'</section>'
            if surgery['status']=='em_curso':content+='<section><h2>Concluir episódio</h2><p>Exige cirurgião atribuído e pelo menos um consumo. Após concluir, não pode reabrir.</p>'+form('state',unit_id,hidden+'<input type="hidden" name="status" value="concluida">','Concluir cirurgia','detalhe')+'</section>'
            if surgery['status']=='agendada':content+='<section><h2>Cancelar episódio agendado</h2>'+form('state',unit_id,hidden+'<input type="hidden" name="status" value="cancelada">','Cancelar cirurgia','detalhe')+'</section>'
            consumptions=con.execute('SELECT c.*,i.name FROM consumption c JOIN item i USING(item_id) WHERE surgery_id=? ORDER BY consumption_id',(detail_id,)).fetchall()
            content+='<section><h2>Histórico de consumos</h2>'+table(['Recurso','Quantidade','Custo unitário','Motivo','Registo UTC'],[(esc(r['name']),r['quantity'],money(r['unit_cost_cents']),esc(r['reason'] or '—'),esc(r['recorded_at'])) for r in consumptions])+'</section>'
    nav=[('/','Painel'),('/orcamentos','Orçamentos'),('/procedimentos','Preços avulsos'),('/pacotes','Pacotes'),('/medicos','Médicos'),('/pacientes','Pacientes')]
    options=''.join(f'<option value="{u["unit_id"]}" '+('selected' if u['unit_id']==unit_id else '')+f'>{esc(u["name"])}</option>' for u in units)
    return '<!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+' · Cirurgia Controle</title><link rel="stylesheet" href="/style.css"></head><body><aside><a class="brand" href="/?unit_id='+str(unit_id)+'"><span>CC</span> Cirurgia Controle</a><p class="nav-label">GESTÃO CIRÚRGICA</p><nav>'+''.join(f'<a class="'+('active' if path==url or (path=='/detalhe' and url=='/orcamentos') else '')+f'" href="{url}?unit_id={unit_id}">{name}</a>' for url,name in nav)+'</nav><div class="aside-foot">Projeto académico<br>Dados inteiramente fictícios<br><b>Modelação de Dados · 2026</b></div></aside><div class="workspace"><header><span>Visão da unidade</span><form method="get" action="'+('/orcamentos' if path=='/detalhe' else path)+'"><label class="sr-only" for="unit">Unidade</label><select id="unit" name="unit_id" onchange="this.form.submit()">'+options+'</select><button class="secondary">Selecionar</button></form></header><main><div class="page-heading"><div><span class="eyebrow">'+esc(unit['city'])+' · '+esc(unit['code'])+'</span><h1>'+title+'</h1><p>'+subtitle+'</p></div><span class="badge">EUR · simulação</span></div>'+('<p class="notice" role="status">'+esc(message)+'</p>' if message else '')+content+'<footer>Cirurgia Controle 1.0 · Execução local sem autenticação · Preços e recursos simulados</footer></main></div></body></html>'


def search(path,unit_id,q):
    return f'<form class="search" method="get" action="{path}"><input type="hidden" name="unit_id" value="{unit_id}"><label class="sr-only" for="q">Pesquisar</label><input id="q" name="q" value="{esc(q)}" placeholder="Pesquisar nome, código, procedimento ou estado"><button>Pesquisar</button></form>'


def episode_table(rows,unit_id):
    return table(['Episódio','Paciente / procedimento','Estado','Previsto','Real','Desvio','Ação'],[(f'#{r["surgery_id"]}',esc(r['patient_name'])+'<small>'+esc(r['procedure_name'])+'</small>',f'<span class="badge {esc(r["status"])}">{esc(r["status"])}</span>',money(r['planned_cents']),money(r['actual_cents']),money(r['variance_cents']),f'<a href="/detalhe?unit_id={unit_id}&id={r["surgery_id"]}">Abrir →</a>') for r in rows])


def dispatch(data,action):
    unit_id=int(data['unit_id'])
    with connect() as con:require_unit(con,unit_id)
    if action=='create':
        lines=[(int(k[4:]),v) for k,v in data.items() if k.startswith('qty_') and v.strip() and Decimal(v.replace(',','.'))!=0]
        return create_surgery(unit_id,int(data['patient_id']),int(data['procedure_id']),data['scheduled_at'],data['modality'],int(data['package_id']) if data.get('package_id') else None,lines)
    if action=='approve':approve_budget(unit_id,int(data['budget_id']))
    elif action=='consume':record_consumption(unit_id,int(data['surgery_id']),int(data['item_id']),data['quantity'],data.get('reason',''))
    elif action=='state':change_state(unit_id,int(data['surgery_id']),data['status'])
    elif action=='assign':assign_doctor(unit_id,int(data['surgery_id']),int(data['doctor_id']),data['role'])
    elif action=='patient':
        with connect() as con:con.execute('INSERT INTO patient(name,fictional_code) VALUES(?,?)',(text(data['name']),text(data['code'],40)))
    elif action=='doctor':
        with connect() as con:
            doctor_id=con.execute('INSERT INTO doctor(name,registration) VALUES(?,?)',(text(data['name']),text(data['registration'],40))).lastrowid
            con.execute('INSERT INTO doctor_specialty VALUES(?,?)',(doctor_id,int(data['specialty_id'])))
            con.execute('INSERT INTO doctor_unit VALUES(?,?)',(doctor_id,unit_id))
    elif action=='doctor-link':
        with connect() as con:con.execute('INSERT INTO doctor_unit VALUES(?,?)',(int(data['doctor_id']),unit_id))
    elif action=='price':
        price=cents(data['price'])
        if price<=0:raise ValueError('O preço deve ser positivo.')
        with connect() as con:
            changed=con.execute('UPDATE unit_procedure_price SET sale_price_cents=? WHERE unit_id=? AND procedure_id=?',(price,unit_id,int(data['procedure_id']))).rowcount
            if changed!=1:raise ValueError('Referência de preço inexistente.')
    else:raise LookupError('Operação inexistente.')
    return int(data.get('surgery_id') or 0)


class Handler(BaseHTTPRequestHandler):
    def send_content(self,body,status=200,kind='text/html; charset=utf-8'):
        payload=body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(payload)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        url=urlsplit(self.path); args={k:v[0] for k,v in parse_qs(url.query).items()}
        if url.path=='/style.css':return self.send_content((ROOT/'application/style.css').read_text(encoding='utf-8'),kind='text/css; charset=utf-8')
        try:self.send_content(render(url.path,int(args.get('unit_id','1')),args.get('q',''),args.get('message',''),int(args['id']) if args.get('id') else None))
        except LookupError as exc:self.send_content('<h1>404</h1><p>'+esc(exc)+'</p>',404)
        except (ValueError,OverflowError,sqlite3.Error) as exc:self.send_content('<h1>Pedido inválido</h1><p>'+esc(exc)+'</p><a href="/">Voltar</a>',400)

    def do_POST(self):
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>65536:raise ValueError('Tamanho de pedido inválido.')
            data={k:v[0] for k,v in parse_qs(self.rfile.read(length).decode('utf-8'),keep_blank_values=True).items()}
            episode=dispatch(data,urlsplit(self.path).path.strip('/'))
            back=data.get('back','orcamentos')
            if back not in ('detalhe','orcamentos','pacientes','medicos','procedimentos'):back='orcamentos'
            if episode:back='detalhe'
            query={'unit_id':int(data['unit_id']),'message':'Operação guardada com sucesso.'}
            if episode:query['id']=episode
            self.send_response(303);self.send_header('Location','/'+back+'?'+urlencode(query));self.end_headers()
        except (ValueError,OverflowError,KeyError,sqlite3.Error,InvalidOperation,LookupError) as exc:
            self.send_content('<!doctype html><html lang="pt"><meta charset="utf-8"><link rel="stylesheet" href="/style.css"><main><section><h1>Operação rejeitada</h1><p role="alert">'+esc(exc)+'</p><p>Não foi guardada uma operação parcial. Use o botão Voltar do navegador para rever os campos.</p><a href="/">Voltar ao painel</a></section></main></html>',400)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--init',action='store_true');parser.add_argument('--port',type=int,default=8000);parser.add_argument('--db',type=Path);args=parser.parse_args()
    if args.db:DB=args.db.resolve()
    if args.init:
        initialize();print('Base fictícia criada:',DB)
    else:
        if not DB.exists():raise SystemExit('Inicialize primeiro: python application/app.py --init')
        print(f'Abra http://127.0.0.1:{args.port}',flush=True)
        ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

