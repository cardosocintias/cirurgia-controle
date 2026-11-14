"""Verificação alargada de serviços e HTTP em cópias temporárias."""
import unittest,sqlite3,json,threading,http.client
from datetime import datetime
from urllib.parse import urlencode
from test_project import ProjectTests
import app


class AcceptanceTests(unittest.TestCase):
    setUpClass=ProjectTests.__dict__['setUpClass']
    tearDownClass=ProjectTests.__dict__['tearDownClass']
    setUp=ProjectTests.setUp
    tearDown=ProjectTests.tearDown
    new=ProjectTests.new
    budget=ProjectTests.budget
    reject=ProjectTests.reject

    def test_money_rejects_invalid(self):
        for value in ['NaN','inf','-0.01','1.001','abc','10000000.01']:
            with self.subTest(value=value),self.assertRaises(ValueError):app.cents(value)
    def test_money_decimal_exact(self):
        for value,expected in [('0.01',1),('1,23',123),('999.99',99999)]:self.assertEqual(app.cents(value),expected)
    def test_patient_create_duplicate_and_blank(self):
        app.dispatch({'unit_id':'2','name':'Teste Aceitação','code':'ACC-001'},'patient')
        with app.connect() as c:self.assertEqual(c.execute("SELECT COUNT(*) FROM patient WHERE fictional_code='ACC-001'").fetchone()[0],1)
        with self.assertRaises(sqlite3.IntegrityError):app.dispatch({'unit_id':'2','name':'Duplicado','code':'ACC-001'},'patient')
        with self.assertRaises(ValueError):app.dispatch({'unit_id':'2','name':' ','code':'ACC-002'},'patient')
    def test_doctor_create_and_rollback(self):
        app.dispatch({'unit_id':'3','name':'Médico Aceitação','registration':'ACC-M01','specialty_id':'1'},'doctor')
        with app.connect() as c:
            doctor=c.execute("SELECT doctor_id FROM doctor WHERE registration='ACC-M01'").fetchone()[0]
            self.assertIsNotNone(c.execute('SELECT 1 FROM doctor_unit WHERE doctor_id=? AND unit_id=3',(doctor,)).fetchone())
        with self.assertRaises(sqlite3.IntegrityError):app.dispatch({'unit_id':'1','name':'Inválido','registration':'ACC-M02','specialty_id':'9999'},'doctor')
        with app.connect() as c:self.assertEqual(c.execute("SELECT COUNT(*) FROM doctor WHERE registration='ACC-M02'").fetchone()[0],0)
    def test_doctor_link_duplicate(self):
        app.dispatch({'unit_id':'3','doctor_id':'1'},'doctor-link')
        with self.assertRaises(sqlite3.IntegrityError):app.dispatch({'unit_id':'3','doctor_id':'1'},'doctor-link')
    def test_prices_only_selected_unit(self):
        with app.connect() as c:old=c.execute('SELECT sale_price_cents FROM unit_procedure_price WHERE procedure_id=100 AND unit_id=1').fetchone()[0]
        app.dispatch({'unit_id':'2','procedure_id':'100','price':'2222.22'},'price')
        with app.connect() as c:
            self.assertEqual(c.execute('SELECT sale_price_cents FROM unit_procedure_price WHERE procedure_id=100 AND unit_id=2').fetchone()[0],222222)
            self.assertEqual(c.execute('SELECT sale_price_cents FROM unit_procedure_price WHERE procedure_id=100 AND unit_id=1').fetchone()[0],old)
    def test_price_flows_into_new_budget(self):
        app.dispatch({'unit_id':'2','procedure_id':'100','price':'2222.22'},'price')
        sid=app.create_surgery(2,1,100,'2026-11-01T10:00','avulso',lines=[(2,1)])
        with app.connect() as c:self.assertEqual(c.execute('SELECT sale_price_cents FROM budget WHERE surgery_id=?',(sid,)).fetchone()[0],222222)
    def test_package_price_is_independent(self):
        app.dispatch({'unit_id':'1','procedure_id':'1','price':'7777'},'price')
        sid=app.create_surgery(1,1,1,'2026-11-01T10:00','pacote',1)
        with app.connect() as c:self.assertEqual(c.execute('SELECT sale_price_cents FROM budget WHERE surgery_id=?',(sid,)).fetchone()[0],500000)
    def test_cannot_remove_used_doctor_unit(self):self.reject('DELETE FROM doctor_unit WHERE doctor_id=1 AND unit_id=1')
    def test_cannot_change_used_doctor_unit(self):self.reject('UPDATE doctor_unit SET unit_id=2 WHERE doctor_id=1 AND unit_id=1')
    def test_cannot_change_used_specialty(self):self.reject('UPDATE doctor_specialty SET specialty_id=3 WHERE doctor_id=1 AND specialty_id=1')
    def test_cannot_change_procedure_specialty_with_team(self):self.reject('UPDATE surgical_procedure SET specialty_id=3 WHERE procedure_id=1')
    def test_integer_money_sql(self):
        self.reject("INSERT INTO item VALUES(999,'Inválido texto','material','unidade','abc')")
        self.reject("INSERT INTO item VALUES(999,'Inválido fração','material','unidade',1.5)")
    def test_quantity_sql(self):
        self.reject("INSERT INTO package_item VALUES(1,11,'abc')")
        self.reject('INSERT INTO package_item VALUES(1,11,0.0001)')
    def test_no_budget_detail_handled(self):
        with app.connect() as c:sid=c.execute("INSERT INTO surgery(unit_id,patient_id,procedure_id,scheduled_at,status) VALUES(1,1,1,'2026-11-01T10:00','agendada')").lastrowid
        with self.assertRaises(ValueError):app.render('/detalhe',1,detail_id=sid)
    def test_schedule_requires_local_minutes(self):
        for value in ['20261101','2026-11-01','2026-11-01T10:00+02:00','2026-11-01T10:00:01']:
            with self.subTest(date=value),self.assertRaises(ValueError):app.create_surgery(1,1,1,value,'avulso',lines=[(2,1)])
    def test_empty_avulso(self):
        with self.assertRaises(ValueError):app.create_surgery(1,1,1,'2026-11-01T10:00','avulso',lines=[])
    def test_duplicate_resources_rollback(self):
        with app.connect() as c:before=c.execute('SELECT COUNT(*) FROM surgery').fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):app.create_surgery(1,1,1,'2026-11-01T10:00','avulso',lines=[(2,1),(2,1)])
        with app.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM surgery').fetchone()[0],before)
    def test_long_consumption_reason(self):
        sid=self.new();app.approve_budget(1,self.budget(sid))
        with self.assertRaises(ValueError):app.record_consumption(1,sid,2,1,'x'*501)
    def test_cancelled_surgery_rejects_team_and_consumption(self):
        sid=self.new();app.approve_budget(1,self.budget(sid));app.change_state(1,sid,'cancelada')
        with self.assertRaises(sqlite3.IntegrityError):app.assign_doctor(1,sid,1,'cirurgiao')
        with self.assertRaises(sqlite3.IntegrityError):app.record_consumption(1,sid,2,1)
    def test_team_rejected_after_start(self):
        sid=self.new();app.approve_budget(1,self.budget(sid));app.record_consumption(1,sid,2,1)
        with self.assertRaises(sqlite3.IntegrityError):app.assign_doctor(1,sid,1,'cirurgiao')
    def test_invalid_role(self):
        with self.assertRaises(ValueError):app.assign_doctor(1,self.new(),1,'outro')
    def test_queries_have_expected_results(self):
        with app.connect() as c:
            self.assertEqual([tuple(r) for r in c.execute('SELECT unit_id,COUNT(*) FROM surgery GROUP BY unit_id')],[(1,83),(2,80),(3,80)])
            self.assertEqual(c.execute('SELECT COUNT(*) FROM v_surgery_financial WHERE status=\'concluida\' AND variance_cents>0').fetchone()[0],40)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM v_cost_variance WHERE actual_quantity>0 AND planned_quantity=0').fetchone()[0],40)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM unit_procedure_price').fetchone()[0],171)
    def test_search_all_sections(self):
        for path in ['/procedimentos','/pacotes','/medicos','/pacientes','/orcamentos']:
            page=app.render(path,3,q='SEM-RESULTADO-XYZ');self.assertIn('Sem registos para este filtro.',page)
    def test_units_invalid(self):
        with self.assertRaises(ValueError):app.render('/',9999)
    def test_rounding_multiple_consumptions_same_resource(self):
        sid=self.new();app.approve_budget(1,self.budget(sid))
        with app.connect() as c:
            for _ in range(3):c.execute('INSERT INTO consumption(surgery_id,item_id,quantity,unit_cost_cents) VALUES(?,2,.5,1)',(sid,))
            self.assertEqual(c.execute('SELECT actual_cents FROM v_cost_variance WHERE surgery_id=? AND item_id=2',(sid,)).fetchone()[0],3)


class QuietHandler(app.Handler):
    def log_message(self,*args):pass


class HTTPTests(AcceptanceTests):
    # Only run the explicit HTTP methods in this class; the runner excludes inherited service cases.
    def setUp(self):
        super().setUp();self.server=app.ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();super().tearDown()
    def request(self,method,path,data=None,headers=None,raw=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        body=raw if raw is not None else urlencode(data) if data is not None else None
        try:
            c.request(method,path,body=body,headers=headers or {});r=c.getresponse();return r.status,dict(r.getheaders()),r.read().decode('utf-8')
        finally:c.close()
    def test_http_pages_all_units(self):
        for unit in [1,2,3]:
            for path in ['/','/orcamentos','/procedimentos','/pacotes','/medicos','/pacientes']:
                status,headers,body=self.request('GET',path+'?unit_id='+str(unit));self.assertEqual(status,200);self.assertIn('text/html',headers['Content-Type']);self.assertIn('<html lang="pt">',body)
    def test_http_invalid_ids(self):
        for path in ['/?unit_id=abc','/?unit_id=999','/detalhe?unit_id=1&id=9999999999999999999999999','/detalhe?unit_id=1&id=-1','/detalhe?unit_id=1&id=xyz']:
            with self.subTest(path=path):self.assertEqual(self.request('GET',path)[0],400)
    def test_http_404_and_css(self):
        self.assertEqual(self.request('GET','/nao-existe')[0],404)
        status,headers,body=self.request('GET','/style.css');self.assertEqual(status,200);self.assertIn('text/css',headers['Content-Type'])
    def test_http_missing_form_and_bad_utf8(self):
        self.assertEqual(self.request('POST','/patient',{'unit_id':'1'})[0],400)
        self.assertEqual(self.request('POST','/patient',raw=b'\xff')[0],400)
        self.assertEqual(self.request('POST','/patient',raw=b'')[0],400)
    def test_http_patient_create_redirect(self):
        status,headers,_=self.request('POST','/patient',{'unit_id':'3','name':'HTTP Teste','code':'HTTP-001','back':'pacientes'})
        self.assertEqual(status,303);self.assertIn('/pacientes?unit_id=3',headers['Location'])
        self.assertIn('HTTP Teste',self.request('GET',headers['Location'])[2])
    def test_http_duplicate_patient(self):
        self.assertEqual(self.request('POST','/patient',{'unit_id':'1','name':'HTTP Teste','code':'FIC-001'})[0],400)
    def test_http_unknown_operation(self):self.assertEqual(self.request('POST','/fake',{'unit_id':'1'})[0],400)
    def test_http_budget_flow(self):
        status,h,_=self.request('POST','/create',{'unit_id':'1','patient_id':'1','procedure_id':'1','scheduled_at':'2026-11-01T10:00','modality':'avulso','qty_2':'1.5'})
        self.assertEqual(status,303);self.assertIn('/detalhe?',h['Location']);self.assertIn('rascunho',self.request('GET',h['Location'])[2])
        with app.connect() as c:sid=c.execute('SELECT MAX(surgery_id) FROM surgery').fetchone()[0]
        for action,data in [('assign',{'doctor_id':'1','role':'cirurgiao'}),('approve',{'budget_id':str(self.budget(sid))}),('consume',{'item_id':'2','quantity':'1.5','reason':'Teste HTTP'}),('state',{'status':'concluida'})]:
            data.update(unit_id='1',surgery_id=str(sid),back='detalhe');self.assertEqual(self.request('POST','/'+action,data)[0],303)
        with app.connect() as c:self.assertEqual(tuple(c.execute('SELECT status,actual_cents FROM v_surgery_financial WHERE surgery_id=?',(sid,)).fetchone()),('concluida',60000))
    def test_http_post_invalid_quantity(self):
        for amount in ['NaN','inf','abc','-1','0.0001']:
            self.assertEqual(self.request('POST','/consume',{'unit_id':'1','surgery_id':'1','item_id':'2','quantity':amount})[0],400)
    def test_http_cross_unit_post(self):self.assertEqual(self.request('POST','/approve',{'unit_id':'2','budget_id':'3'})[0],400)
    def test_http_xss_message(self):
        body=self.request('GET','/?message=%3Cscript%3Ealert(1)%3C/script%3E')[2];self.assertNotIn('<script>alert(1)</script>',body);self.assertIn('&lt;script&gt;',body)


if __name__=='__main__':
    service=unittest.defaultTestLoader.loadTestsFromTestCase(AcceptanceTests)
    http_suite=unittest.TestSuite(HTTPTests(name) for name in HTTPTests.__dict__ if name.startswith('test_http_'))
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([service,http_suite]))
    facts={'date':datetime.now().isoformat(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'failed_cases':[str(case) for case,_ in result.failures+result.errors]}
    (app.ROOT/'documentation/acceptance-results.json').write_text(json.dumps(facts,indent=2,ensure_ascii=False),encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
