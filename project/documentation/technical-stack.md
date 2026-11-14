# Tecnologias e arquitetura da versão 1.0

Base: SQLite 3.53.1; dialeto SQLite, PRAGMA foreign_keys=ON em cada ligação. Backend: Python 3.12.14, compatível com Python 3.13, biblioteca padrão. HTML, CSS e JavaScript nativo; sem ORM nem dependências externas para executar a aplicação. Arquitetura: navegador → HTTP local → serviços Python → data/cirurgias.db. Servidor ThreadingHTTPServer ligado apenas a 127.0.0.1. Porta padrão 8000; --port permite outra porta e --db uma cópia para demonstração.

O SGBD escolhido para esta entrega é SQLite. Todas as 17 tabelas são STRICT (SQLite 3.37 ou superior), rejeitando texto e frações em campos monetários inteiros. A persistência é a mesma base entregue e reconstruível a partir de seis scripts SQL. Não há fontes ocultas. Inicialização: schema, views, programmable_objects, seed, catalog e demo. Construção primeiro em memória, depois backup SQLite para destino novo. Recusa sobrescrever base existente.

Dinheiro em cêntimos inteiros. Quantidades REAL limitadas a três casas e verificadas com Decimal no serviço. Cada produto de quantidade por custo é arredondado ao cêntimo antes da soma; produtos não negativos usam metade para cima. Ambos os relatórios usam a mesma regra. Esta opção foi testada com meios cêntimos; não é uma implementação de contabilidade fiscal.

Ferramentas documentais de geração: reportlab, pypdfium2, Pillow e @oai/artifact-tool no ambiente de autoria. Não são dependências da aplicação do professor. Segredos e credenciais não são necessários. O servidor local não é uma implantação de produção.
