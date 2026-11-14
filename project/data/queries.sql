-- Q01: comparação global, incluindo desvio percentual e margem.
SELECT * FROM v_surgery_financial;
-- Q02: cirurgias concluídas acima do orçamento.
SELECT * FROM v_surgery_financial WHERE status='concluida' AND variance_cents>0;
-- Q03: desvio por procedimento, apenas casos concluídos com orçamento.
SELECT procedure_name,COUNT(*) total,AVG(variance_cents)/100.0 average_variance_eur
FROM v_surgery_financial WHERE status='concluida' AND planned_cents IS NOT NULL GROUP BY procedure_name;
-- Q04: componentes que mais contribuem para o desvio das cirurgias concluídas.
SELECT v.category,SUM(v.actual_cents-v.planned_cents)/100.0 variance_eur
FROM v_cost_variance v JOIN surgery s USING(surgery_id) WHERE s.status='concluida'
GROUP BY v.category ORDER BY variance_eur DESC;
-- Q05: profissionais e especialidades (N:M).
SELECT d.name,e.name specialty FROM doctor d JOIN doctor_specialty ds USING(doctor_id) JOIN specialty e USING(specialty_id);
-- Q06: cirurgias com custo superior à média dos casos concluídos (subconsulta).
SELECT * FROM v_surgery_financial WHERE status='concluida' AND actual_cents >
(SELECT AVG(actual_cents) FROM v_surgery_financial WHERE status='concluida');
-- Q07: artigos consumidos sem previsão no orçamento aprovado.
SELECT v.* FROM v_cost_variance v WHERE actual_quantity>0 AND planned_quantity=0
AND EXISTS(SELECT 1 FROM budget b WHERE b.surgery_id=v.surgery_id AND b.status='aprovado');
-- Q08: composição e custo atual de cada pacote.
SELECT p.name,SUM(ROUND(pi.quantity*i.unit_cost_cents))/100.0 cost_eur,p.sale_price_cents/100.0 price_eur
FROM package p JOIN package_item pi USING(package_id) JOIN item i USING(item_id) GROUP BY p.package_id;
-- Q09: agenda com paciente e equipa, incluindo cirurgias sem equipa.
SELECT s.surgery_id,s.scheduled_at,p.name patient,GROUP_CONCAT(d.name, ', ') team
FROM surgery s JOIN patient p USING(patient_id) LEFT JOIN surgery_doctor sd USING(surgery_id)
LEFT JOIN doctor d USING(doctor_id) WHERE s.status='agendada' GROUP BY s.surgery_id;
-- Q10: frequência dos motivos de consumo adicional.
SELECT reason,COUNT(*) occurrences FROM consumption WHERE reason IS NOT NULL GROUP BY reason;
-- Q11: indicadores concluídos por unidade, sem somar episódios parciais.
SELECT unit_id,unit_name,COUNT(*) surgeries,SUM(planned_cents)/100.0 planned_eur,
 SUM(actual_cents)/100.0 actual_eur,SUM(variance_cents)/100.0 variance_eur
FROM v_surgery_financial WHERE status='concluida' GROUP BY unit_id,unit_name;
-- Q12: comparação de preços avulsos entre unidades.
SELECT p.name,u.name unit_name,up.sale_price_cents/100.0 price_eur
FROM unit_procedure_price up JOIN unit u USING(unit_id)
JOIN surgical_procedure p USING(procedure_id) ORDER BY p.name,u.name;

