CREATE TRIGGER budget_requires_lines BEFORE UPDATE OF status ON budget
WHEN NEW.status='aprovado' AND NOT EXISTS(SELECT 1 FROM budget_line WHERE budget_id=NEW.budget_id)
BEGIN SELECT RAISE(ABORT,'Orçamento aprovado requer linhas.'); END;
CREATE TRIGGER budget_insert_draft BEFORE INSERT ON budget WHEN NEW.status <> 'rascunho'
BEGIN SELECT RAISE(ABORT,'Crie primeiro um orçamento em rascunho.'); END;
CREATE TRIGGER budget_lock_update BEFORE UPDATE ON budget WHEN OLD.status <> 'rascunho'
BEGIN SELECT RAISE(ABORT,'Orçamento aprovado é imutável nesta versão.'); END;
CREATE TRIGGER budget_lock_delete BEFORE DELETE ON budget WHEN OLD.status <> 'rascunho'
BEGIN SELECT RAISE(ABORT,'Orçamento aprovado é imutável.'); END;
CREATE TRIGGER line_lock_insert BEFORE INSERT ON budget_line
WHEN (SELECT status FROM budget WHERE budget_id=NEW.budget_id) <> 'rascunho'
BEGIN SELECT RAISE(ABORT,'Linhas aprovadas são imutáveis.'); END;
CREATE TRIGGER line_lock_update BEFORE UPDATE ON budget_line
WHEN (SELECT status FROM budget WHERE budget_id=OLD.budget_id) <> 'rascunho'
 OR (SELECT status FROM budget WHERE budget_id=NEW.budget_id) <> 'rascunho'
BEGIN SELECT RAISE(ABORT,'Linhas aprovadas são imutáveis.'); END;
CREATE TRIGGER line_lock_delete BEFORE DELETE ON budget_line
WHEN (SELECT status FROM budget WHERE budget_id=OLD.budget_id) <> 'rascunho'
BEGIN SELECT RAISE(ABORT,'Linhas aprovadas são imutáveis.'); END;
CREATE TRIGGER consumption_allowed BEFORE INSERT ON consumption
WHEN NOT EXISTS(SELECT 1 FROM budget WHERE surgery_id=NEW.surgery_id AND status='aprovado')
 OR (SELECT status FROM surgery WHERE surgery_id=NEW.surgery_id) NOT IN ('agendada','em_curso')
BEGIN SELECT RAISE(ABORT,'Consumo requer orçamento aprovado e cirurgia aberta.'); END;
CREATE TRIGGER consumption_starts_surgery AFTER INSERT ON consumption
BEGIN UPDATE surgery SET status='em_curso' WHERE surgery_id=NEW.surgery_id AND status='agendada'; END;

-- Consumos representam factos históricos imutáveis. Correção por estorno é evolução futura.
CREATE TRIGGER consumption_no_update BEFORE UPDATE ON consumption
BEGIN SELECT RAISE(ABORT,'Consumos são imutáveis nesta versão.'); END;
CREATE TRIGGER consumption_no_delete BEFORE DELETE ON consumption
BEGIN SELECT RAISE(ABORT,'Consumos são imutáveis nesta versão.'); END;
CREATE TRIGGER surgery_initial BEFORE INSERT ON surgery WHEN NEW.status<>'agendada'
BEGIN SELECT RAISE(ABORT,'A cirurgia começa agendada.'); END;
CREATE TRIGGER surgery_transition BEFORE UPDATE OF status ON surgery
WHEN NEW.status<>OLD.status AND NOT (
 (OLD.status='agendada' AND NEW.status IN ('em_curso','cancelada')) OR
 (OLD.status='em_curso' AND NEW.status='concluida'))
BEGIN SELECT RAISE(ABORT,'Transição de estado inválida.'); END;
CREATE TRIGGER surgery_start BEFORE UPDATE OF status ON surgery
WHEN NEW.status='em_curso' AND NOT EXISTS(SELECT 1 FROM budget WHERE surgery_id=NEW.surgery_id AND status='aprovado')
BEGIN SELECT RAISE(ABORT,'Iniciar exige orçamento aprovado.'); END;
CREATE TRIGGER surgery_finish BEFORE UPDATE OF status ON surgery
WHEN NEW.status='concluida' AND (NOT EXISTS(SELECT 1 FROM consumption WHERE surgery_id=NEW.surgery_id)
 OR NOT EXISTS(SELECT 1 FROM surgery_doctor WHERE surgery_id=NEW.surgery_id AND role='cirurgiao'))
BEGIN SELECT RAISE(ABORT,'Concluir exige consumo e cirurgião atribuído.'); END;
CREATE TRIGGER surgery_identity BEFORE UPDATE OF patient_id,procedure_id,unit_id ON surgery
BEGIN SELECT RAISE(ABORT,'Identificação do episódio é imutável.'); END;
CREATE TRIGGER surgery_no_delete BEFORE DELETE ON surgery
BEGIN SELECT RAISE(ABORT,'Use cancelamento; episódios não são apagados.'); END;
CREATE TRIGGER budget_transition BEFORE UPDATE OF status ON budget
WHEN NEW.status<>OLD.status AND NOT (OLD.status='rascunho' AND NEW.status='aprovado')
BEGIN SELECT RAISE(ABORT,'Só é permitida aprovação do rascunho.'); END;
CREATE TRIGGER budget_open BEFORE UPDATE OF status ON budget
WHEN NEW.status='aprovado' AND (SELECT status FROM surgery WHERE surgery_id=NEW.surgery_id)<>'agendada'
BEGIN SELECT RAISE(ABORT,'Aprovação exige cirurgia agendada.'); END;
CREATE TRIGGER budget_package_insert BEFORE INSERT ON budget
WHEN NEW.modality='pacote' AND NOT EXISTS(
 SELECT 1 FROM package p JOIN surgery s ON s.surgery_id=NEW.surgery_id
 WHERE p.package_id=NEW.package_id AND p.procedure_id=s.procedure_id AND p.unit_id=s.unit_id)
BEGIN SELECT RAISE(ABORT,'Pacote incompatível com unidade ou procedimento.'); END;
CREATE TRIGGER budget_identity BEFORE UPDATE OF surgery_id,package_id,modality,version ON budget
BEGIN SELECT RAISE(ABORT,'Identificação do orçamento é imutável.'); END;
CREATE TRIGGER team_eligible BEFORE INSERT ON surgery_doctor WHEN NOT EXISTS(
 SELECT 1 FROM surgery s JOIN surgical_procedure sp USING(procedure_id)
 JOIN doctor_specialty ds ON ds.specialty_id=sp.specialty_id AND ds.doctor_id=NEW.doctor_id
 JOIN doctor_unit du ON du.doctor_id=ds.doctor_id AND du.unit_id=s.unit_id
 WHERE s.surgery_id=NEW.surgery_id AND s.status='agendada')
BEGIN SELECT RAISE(ABORT,'Médico incompatível com unidade/especialidade ou episódio iniciado.'); END;
CREATE TRIGGER team_no_update BEFORE UPDATE ON surgery_doctor
BEGIN SELECT RAISE(ABORT,'Participação médica imutável nesta versão.'); END;
CREATE TRIGGER team_no_delete BEFORE DELETE ON surgery_doctor
BEGIN SELECT RAISE(ABORT,'Participação médica imutável nesta versão.'); END;
CREATE TRIGGER package_identity BEFORE UPDATE OF unit_id,procedure_id ON package
BEGIN SELECT RAISE(ABORT,'Identificação do pacote é imutável.'); END;
CREATE TRIGGER doctor_unit_lock BEFORE DELETE ON doctor_unit
WHEN EXISTS(SELECT 1 FROM surgery_doctor sd JOIN surgery s USING(surgery_id) WHERE sd.doctor_id=OLD.doctor_id AND s.unit_id=OLD.unit_id)
BEGIN SELECT RAISE(ABORT,'Vínculo usado em cirurgia.'); END;
CREATE TRIGGER doctor_specialty_lock BEFORE DELETE ON doctor_specialty
WHEN EXISTS(SELECT 1 FROM surgery_doctor sd JOIN surgery s USING(surgery_id) JOIN surgical_procedure sp USING(procedure_id) WHERE sd.doctor_id=OLD.doctor_id AND sp.specialty_id=OLD.specialty_id)
BEGIN SELECT RAISE(ABORT,'Especialidade usada em cirurgia.'); END;

-- Preservar elegibilidade após alterações dos catálogos por SQL.
CREATE TRIGGER doctor_unit_update_lock BEFORE UPDATE ON doctor_unit
WHEN EXISTS(SELECT 1 FROM surgery_doctor sd JOIN surgery s USING(surgery_id)
 WHERE sd.doctor_id=OLD.doctor_id AND s.unit_id=OLD.unit_id)
BEGIN SELECT RAISE(ABORT,'Vínculo usado em cirurgia não pode ser alterado.'); END;
CREATE TRIGGER doctor_specialty_update_lock BEFORE UPDATE ON doctor_specialty
WHEN EXISTS(SELECT 1 FROM surgery_doctor sd JOIN surgery s USING(surgery_id)
 JOIN surgical_procedure sp USING(procedure_id)
 WHERE sd.doctor_id=OLD.doctor_id AND sp.specialty_id=OLD.specialty_id)
BEGIN SELECT RAISE(ABORT,'Especialidade usada em cirurgia não pode ser alterada.'); END;
CREATE TRIGGER procedure_specialty_update_lock BEFORE UPDATE OF specialty_id ON surgical_procedure
WHEN NEW.specialty_id<>OLD.specialty_id AND EXISTS(
 SELECT 1 FROM surgery s JOIN surgery_doctor sd USING(surgery_id) WHERE s.procedure_id=OLD.procedure_id)
BEGIN SELECT RAISE(ABORT,'Procedimento com equipa atribuída não pode mudar de especialidade.'); END;
