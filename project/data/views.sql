-- Agregar orçamento e realização separadamente evita multiplicar linhas nos JOINs.
CREATE VIEW v_surgery_financial AS
WITH planned AS (
 SELECT b.surgery_id,b.sale_price_cents,
 CAST(SUM(ROUND(bl.quantity*bl.unit_cost_cents)) AS INTEGER) AS planned_cents
 FROM budget b JOIN budget_line bl USING(budget_id) WHERE b.status='aprovado' GROUP BY b.budget_id
), actual AS (
 SELECT surgery_id,CAST(SUM(ROUND(quantity*unit_cost_cents)) AS INTEGER) actual_cents
 FROM consumption GROUP BY surgery_id
)
SELECT s.surgery_id,s.unit_id,u.name unit_name,b.modality,p.name patient_name,sp.name procedure_name,s.status,s.scheduled_at,
 pl.planned_cents,pl.sale_price_cents,COALESCE(a.actual_cents,0) actual_cents,
 COALESCE(a.actual_cents,0)-pl.planned_cents variance_cents,
 ROUND(100.0*(COALESCE(a.actual_cents,0)-pl.planned_cents)/NULLIF(pl.planned_cents,0),2) variance_percent,
 pl.sale_price_cents-pl.planned_cents planned_margin_cents,
 pl.sale_price_cents-COALESCE(a.actual_cents,0) actual_margin_cents
FROM surgery s JOIN unit u USING(unit_id) LEFT JOIN budget b ON b.surgery_id=s.surgery_id AND b.status='aprovado' JOIN patient p USING(patient_id) JOIN surgical_procedure sp USING(procedure_id)
LEFT JOIN planned pl USING(surgery_id) LEFT JOIN actual a USING(surgery_id);

CREATE VIEW v_cost_variance AS
WITH planned AS (
 SELECT b.surgery_id,bl.item_id,bl.quantity,ROUND(bl.quantity*bl.unit_cost_cents) cost
 FROM budget b JOIN budget_line bl USING(budget_id) WHERE b.status='aprovado'
), actual AS (
 SELECT surgery_id,item_id,SUM(quantity) quantity,SUM(ROUND(quantity*unit_cost_cents)) cost
 FROM consumption GROUP BY surgery_id,item_id
), keys AS (
 SELECT surgery_id,item_id FROM planned UNION SELECT surgery_id,item_id FROM actual
)
SELECT k.surgery_id,k.item_id,i.name item_name,i.category,
 COALESCE(p.quantity,0) planned_quantity,COALESCE(a.quantity,0) actual_quantity,
 CAST(COALESCE(p.cost,0) AS INTEGER) planned_cents,CAST(COALESCE(a.cost,0) AS INTEGER) actual_cents
FROM keys k JOIN item i USING(item_id)
LEFT JOIN planned p ON p.surgery_id=k.surgery_id AND p.item_id=k.item_id
LEFT JOIN actual a ON a.surgery_id=k.surgery_id AND a.item_id=k.item_id;
