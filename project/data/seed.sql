BEGIN;
INSERT INTO unit VALUES(1,'COI','Unidade Coimbra','Coimbra'),(2,'LIS','Unidade Lisboa','Lisboa'),(3,'POR','Unidade Porto','Porto');
INSERT INTO specialty VALUES(1,'Ortopedia'),(2,'Cirurgia geral');
INSERT INTO doctor VALUES(1,'Ana Martins','DEMO-001'),(2,'Pedro Almeida','DEMO-002'),(3,'Sofia Ferreira','DEMO-003');
INSERT INTO doctor_specialty VALUES(1,1),(2,1),(3,2);
INSERT INTO patient VALUES(1,'Maria Silva','FIC-001'),(2,'João Santos','FIC-002'),(3,'Inês Costa','FIC-003');
INSERT INTO surgical_procedure VALUES(1,1,'Artroplastia do joelho — demonstração'),(2,2,'Herniorrafia — demonstração');
INSERT INTO item VALUES
(1,'Honorários de equipa ortopédica','equipa','equipa',120000),
(2,'Utilização de sala','sala','hora',40000),
(3,'Conjunto de materiais ortopédicos','material','conjunto',50000),
(4,'Prótese de joelho fictícia','protese','unidade',150000),
(5,'Material adicional','material','unidade',15000),
(6,'Honorários de equipa de cirurgia geral','equipa','equipa',70000),
(7,'Conjunto de materiais de cirurgia geral','material','conjunto',25000);
INSERT INTO package(package_id,procedure_id,name,sale_price_cents,unit_id) VALUES(1,1,'Pacote joelho padrão',500000,1),(2,2,'Pacote hérnia padrão',200000,1);
INSERT INTO package_item VALUES(1,1,1),(1,2,2),(1,3,1),(1,4,1),(2,6,1),(2,2,1.5),(2,7,1);
INSERT INTO surgery(surgery_id,patient_id,procedure_id,scheduled_at,status,unit_id) VALUES
(1,1,1,'2026-10-10T09:00','agendada',1),(2,2,1,'2026-10-12T09:00','agendada',1),(3,3,2,'2026-11-05T10:00','agendada',1);
INSERT INTO doctor_unit SELECT doctor_id,1 FROM doctor;
INSERT INTO surgery_doctor VALUES(1,1,'cirurgiao'),(1,2,'assistente'),(2,2,'cirurgiao'),(3,3,'cirurgiao');
INSERT INTO budget(budget_id,surgery_id,version,status,sale_price_cents,modality,package_id) VALUES(1,1,1,'rascunho',500000,'pacote',1),(2,2,1,'rascunho',500000,'pacote',1),(3,3,1,'rascunho',200000,'pacote',2);
INSERT INTO budget_line
SELECT b.budget_id,pi.item_id,pi.quantity,i.unit_cost_cents
FROM budget b JOIN surgery s USING(surgery_id) JOIN package p USING(procedure_id)
JOIN package_item pi USING(package_id) JOIN item i USING(item_id);
UPDATE budget SET status='aprovado' WHERE budget_id IN (1,2);
INSERT INTO consumption(surgery_id,item_id,quantity,unit_cost_cents,reason,recorded_at) VALUES
(1,1,1,120000,NULL,'2026-10-19 12:00:00'),(1,2,2.5,40000,'Mais meia hora de sala','2026-10-19 12:00:00'),(1,3,1,50000,NULL,'2026-10-19 12:00:00'),
(1,4,1,150000,NULL,'2026-10-19 12:00:00'),(1,5,1,15000,'Material adicional','2026-10-19 12:00:00'),
(2,1,1,120000,NULL,'2026-10-19 12:00:00'),(2,2,1.5,40000,'Menor tempo de sala','2026-10-19 12:00:00'),(2,3,1,50000,NULL,'2026-10-19 12:00:00'),(2,4,1,150000,NULL,'2026-10-19 12:00:00');
UPDATE surgery SET status='concluida' WHERE surgery_id IN (1,2);
COMMIT;
