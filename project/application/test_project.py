"""Regressões sobre cópia temporária da reconstrução SQL, sem tocar na demonstração."""
import unittest
import sqlite3
import tempfile
import json
from pathlib import Path
from datetime import datetime
import app


class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template=sqlite3.connect(':memory:')
        for name in ('schema','views','programmable_objects','seed','catalog','demo'):
            cls.template.executescript((app.ROOT/f'data/{name}.sql').read_text(encoding='utf-8'))
        cls.template.commit()

    @classmethod
    def tearDownClass(cls):cls.template.close()

    def setUp(self):
        self.folder=tempfile.TemporaryDirectory(dir=app.ROOT/'application')
        self.original=app.DB;app.DB=Path(self.folder.name)/'test.db'
        c=sqlite3.connect(app.DB)
        try:self.template.backup(c)
        finally:c.close()

    def tearDown(self):
        app.DB=self.original;self.folder.cleanup()

    def reject(self,sql,args=()):
        with app.connect() as c:
            with self.assertRaises(sqlite3.IntegrityError):c.execute(sql,args)

    def new(self,unit=1):
        return app.create_surgery(unit,1,1,'2026-11-01T10:00','avulso',lines=[(1,1),(2,2)])

    def budget(self,sid):
        with app.connect() as c:return c.execute('SELECT budget_id FROM budget WHERE surgery_id=?',(sid,)).fetchone()[0]

    def test_counts_integrity(self):
        with app.connect() as c:
            self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
            for table,count in [('unit',3),('patient',123),('doctor',27),('surgery',243),('package',9)]:self.assertEqual(c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],count)

    def test_reference_totals(self):
        with app.connect() as c:
            r=c.execute('SELECT * FROM v_surgery_financial WHERE surgery_id=1').fetchone()
            self.assertEqual((r['planned_cents'],r['actual_cents'],r['variance_cents'],r['actual_margin_cents']),(400000,435000,35000,65000))

    def test_null_composite_keys(self):
        for sql in ['INSERT INTO doctor_specialty VALUES(NULL,1)','INSERT INTO doctor_specialty VALUES(1,NULL)','INSERT INTO package_item VALUES(NULL,1,1)','INSERT INTO package_item VALUES(1,NULL,1)','INSERT INTO surgery_doctor VALUES(NULL,1,\'cirurgiao\')','INSERT INTO surgery_doctor VALUES(1,NULL,\'cirurgiao\')','INSERT INTO budget_line VALUES(NULL,1,1,100)','INSERT INTO budget_line VALUES(1,NULL,1,100)','INSERT INTO doctor_unit VALUES(NULL,1)','INSERT INTO unit_procedure_price VALUES(NULL,1,100)']:
            with self.subTest(sql=sql):self.reject(sql)

    def test_closed_consumption_update(self):self.reject('UPDATE consumption SET quantity=99 WHERE consumption_id=1')
    def test_closed_consumption_delete(self):self.reject('DELETE FROM consumption WHERE consumption_id=1')
    def test_reopen_closed(self):self.reject("UPDATE surgery SET status='agendada' WHERE surgery_id=1")
    def test_invalid_transition(self):self.reject("UPDATE surgery SET status='concluida' WHERE surgery_id=3")
    def test_consumption_closed_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):app.record_consumption(1,1,1,1)
    def test_consumption_without_approval(self):
        with self.assertRaises(sqlite3.IntegrityError):app.record_consumption(1,3,1,1)
    def test_approved_budget_locked(self):
        self.reject('UPDATE budget SET sale_price_cents=1 WHERE budget_id=1')
        self.reject('UPDATE budget_line SET quantity=99 WHERE budget_id=1')
        self.reject('DELETE FROM budget_line WHERE budget_id=1')
    def test_empty_approval(self):
        sid=self.new();bid=self.budget(sid)
        with app.connect() as c:c.execute('DELETE FROM budget_line WHERE budget_id=?',(bid,))
        with self.assertRaises(sqlite3.IntegrityError):app.approve_budget(1,bid)
    def test_approval_missing_and_repeated(self):
        with self.assertRaises(ValueError):app.approve_budget(1,99999)
        with self.assertRaises(ValueError):app.approve_budget(1,1)
    def test_cross_unit_approval(self):
        with self.assertRaises(ValueError):app.approve_budget(2,3)
    def test_cross_unit_consume(self):
        with self.assertRaises(ValueError):app.record_consumption(2,1,1,1)
    def test_cross_unit_detail(self):
        with self.assertRaises(ValueError):app.render('/detalhe',2,detail_id=1)
    def test_wrong_package(self):
        with self.assertRaises(ValueError):app.create_surgery(2,1,1,'2026-11-01T09:00','pacote',1)
        with self.assertRaises(ValueError):app.create_surgery(1,1,100,'2026-11-01T09:00','pacote',1)
    def test_wrong_package_sql(self):
        sid=self.new(2)
        self.reject("INSERT INTO budget(modality,package_id,budget_id,surgery_id,version,status,sale_price_cents) VALUES('pacote',1,9999,?,2,'rascunho',100)",(sid,))
    def test_atomic_rollback_after_partial_insertion(self):
        with app.connect() as c:before=tuple(c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['surgery','budget','budget_line'])
        with self.assertRaises(ValueError):app.create_surgery(1,1,1,'2026-11-01T10:00','avulso',lines=[(1,1),(999999,1)])
        with app.connect() as c:after=tuple(c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['surgery','budget','budget_line'])
        self.assertEqual(before,after)
    def test_full_avulso_flow(self):
        sid=self.new();app.assign_doctor(1,sid,1,'cirurgiao');app.approve_budget(1,self.budget(sid));app.record_consumption(1,sid,2,'0.5','Mais meia hora');app.change_state(1,sid,'concluida')
        with app.connect() as c:
            r=c.execute('SELECT * FROM v_surgery_financial WHERE surgery_id=?',(sid,)).fetchone()
            self.assertEqual((r['status'],r['modality'],r['actual_cents']),('concluida','avulso',20000))
    def test_package_flow(self):
        sid=app.create_surgery(1,1,1,'2026-11-01T10:00','pacote',1)
        app.approve_budget(1,self.budget(sid))
        with app.connect() as c:self.assertEqual(c.execute('SELECT planned_cents FROM v_surgery_financial WHERE surgery_id=?',(sid,)).fetchone()[0],400000)
    def test_finish_requires_surgeon(self):
        sid=self.new();app.approve_budget(1,self.budget(sid));app.record_consumption(1,sid,1,1)
        with self.assertRaises(sqlite3.IntegrityError):app.change_state(1,sid,'concluida')
    def test_doctor_specialty(self):
        sid=self.new()
        with self.assertRaises(sqlite3.IntegrityError):app.assign_doctor(1,sid,3,'cirurgiao')
    def test_doctor_unit(self):
        sid=self.new(2)
        with self.assertRaises(sqlite3.IntegrityError):app.assign_doctor(2,sid,1,'cirurgiao')
    def test_rounding_detail_equals_summary(self):
        sid=self.new();bid=self.budget(sid)
        with app.connect() as c:
            c.execute('UPDATE budget_line SET unit_cost_cents=1,quantity=0.5 WHERE budget_id=?',(bid,))
        app.approve_budget(1,bid)
        with app.connect() as c:
            c.execute('INSERT INTO consumption(surgery_id,item_id,quantity,unit_cost_cents) VALUES(?,1,0.5,1)',(sid,))
            c.execute('INSERT INTO consumption(surgery_id,item_id,quantity,unit_cost_cents) VALUES(?,2,0.5,1)',(sid,))
            summary=c.execute('SELECT planned_cents,actual_cents FROM v_surgery_financial WHERE surgery_id=?',(sid,)).fetchone()
            detail=c.execute('SELECT SUM(planned_cents),SUM(actual_cents) FROM v_cost_variance WHERE surgery_id=?',(sid,)).fetchone()
            self.assertEqual(tuple(summary),(2,2));self.assertEqual(tuple(summary),tuple(detail))
    def test_all_detail_totals(self):
        with app.connect() as c:
            for r in c.execute('SELECT * FROM v_surgery_financial WHERE planned_cents IS NOT NULL').fetchall():
                d=c.execute('SELECT SUM(planned_cents),SUM(actual_cents) FROM v_cost_variance WHERE surgery_id=?',(r['surgery_id'],)).fetchone()
                self.assertEqual(tuple(d),(r['planned_cents'],r['actual_cents']))
    def test_historical_price(self):
        with app.connect() as c:
            before=tuple(c.execute('SELECT planned_cents,actual_cents,sale_price_cents FROM v_surgery_financial WHERE surgery_id=1').fetchone())
            c.execute('UPDATE item SET unit_cost_cents=999999 WHERE item_id=1');c.execute('UPDATE unit_procedure_price SET sale_price_cents=999999 WHERE unit_id=1')
            self.assertEqual(before,tuple(c.execute('SELECT planned_cents,actual_cents,sale_price_cents FROM v_surgery_financial WHERE surgery_id=1').fetchone()))
    def test_quantity_validation(self):
        for x in ['NaN','inf','-1','0','0.0001','1000001','abc']:
            with self.subTest(value=x),self.assertRaises(ValueError):app.quantity(x)
    def test_cancel_prevents_approval(self):
        sid=self.new();app.change_state(1,sid,'cancelada')
        with self.assertRaises(sqlite3.IntegrityError):app.approve_budget(1,self.budget(sid))
    def test_html_all_pages(self):
        for unit in [1,2,3]:
            for path in ['/','/procedimentos','/pacotes','/medicos','/pacientes','/orcamentos']:
                page=app.render(path,unit);self.assertIn('<html lang="pt">',page);self.assertIn('Unidade',page)
    def test_xss(self):
        with app.connect() as c:c.execute("UPDATE patient SET name='<script>alert(1)</script>' WHERE patient_id=1")
        page=app.render('/pacientes');self.assertNotIn('<script>alert(1)</script>',page);self.assertIn('&lt;script&gt;',page)
    def test_query_file(self):
        sql=(app.ROOT/'data/queries.sql').read_text(encoding='utf-8')
        with app.connect() as c:
            for part in sql.split(';'):
                if part.strip():c.execute(part).fetchall()
    def test_unknown_route(self):
        with self.assertRaises(LookupError):app.render('/unknown')


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ProjectTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    out=app.ROOT/'documentation/test-results.json'
    out.write_text(json.dumps({'date':datetime.now().isoformat(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()},indent=2),encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
