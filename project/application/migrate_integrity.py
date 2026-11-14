"""Migração conservadora para tabelas STRICT, com backup e verificação de todos os registos."""
from pathlib import Path
from contextlib import closing
from datetime import datetime
import sqlite3,tempfile,os,json
import app


def migrate():
    backup_dir=app.ROOT/'data/backups';backup_dir.mkdir(exist_ok=True)
    backup=backup_dir/('before-strict-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.db')
    with closing(sqlite3.connect(app.DB)) as source,closing(sqlite3.connect(backup)) as saved:source.backup(saved)
    with closing(sqlite3.connect(backup)) as source:
        tables=[r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY rowid")]
        with tempfile.TemporaryDirectory(dir=app.DB.parent,prefix='migration-') as folder:
            target_file=Path(folder)/'migrated.db'
            with closing(sqlite3.connect(target_file)) as target:
                target.executescript((app.ROOT/'data/schema.sql').read_text(encoding='utf-8'))
                for name in tables:
                    rows=source.execute(f'SELECT * FROM "{name}"').fetchall()
                    if rows:target.executemany(f'INSERT INTO "{name}" VALUES('+','.join('?' for _ in rows[0])+')',rows)
                target.commit()
                for script in ['views','programmable_objects']:target.executescript((app.ROOT/f'data/{script}.sql').read_text(encoding='utf-8'))
                assert target.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                assert target.execute('PRAGMA foreign_key_check').fetchall()==[]
                for name in tables:
                    before=sorted(source.execute(f'SELECT * FROM "{name}"').fetchall(),key=repr)
                    after=sorted(target.execute(f'SELECT * FROM "{name}"').fetchall(),key=repr)
                    assert before==after,'Dados diferentes: '+name
                assert all(row[-1]==1 for row in target.execute('PRAGMA table_list') if row[1] in tables)
                counts={name:target.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in tables}
            os.replace(target_file,app.DB)
    (app.ROOT/'documentation/integrity-migration.json').write_text(json.dumps({'date':datetime.now().isoformat(),'backup':backup.name,'all_rows_preserved':True,'counts':counts,'strict_tables':len(tables)},indent=2),encoding='utf-8')
    print('Migração concluída; todos os registos preservados. Backup:',backup)


if __name__=='__main__':migrate()
