import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const runtime='C:/Users/Jonatan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {instance}=await import(pathToFileURL(runtime+'/@viz-js/viz/dist/viz.js'));
const {default:sharp}=await import(pathToFileURL(runtime+'/sharp/dist/index.mjs'));
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const folder=path.join(root,'documentation/diagrams');
const schema=JSON.parse(await fs.readFile(path.join(folder,'schema.json'),'utf8'));
const viz=await instance();
const groups=[['ERD01-catalogos',['unit','specialty','surgical_procedure','procedure_pricing','unit_procedure_price']],['ERD02-equipa',['doctor','specialty','doctor_specialty','unit','doctor_unit','surgery_doctor']],['ERD03-pacotes',['package','package_item','item','budget']],['ERD04-operacoes',['patient','surgery','budget','budget_line','consumption','item']],['ERD-completo',Object.keys(schema)]];
for(const [name,nodes] of groups){
 let dot='digraph ERD { graph [rankdir=LR, bgcolor="white",nodesep=0.5,ranksep=0.9,pad=0.2,splines=polyline]; node [shape=plain,fontname="Arial"]; edge [fontname="Arial",fontsize=11,color="#5b7d8b",arrowsize=0.8];\n';
 for(const n of nodes){
  const s=schema[n];
  let label='<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" COLOR="#a8bcc7"><TR><TD BGCOLOR="#17394a"><FONT COLOR="white" POINT-SIZE="15"><B>'+n+'</B></FONT></TD></TR>';
  for(const c of s.columns){const fk=s.fk.some(f=>f.from===c.name);label+='<TR><TD ALIGN="LEFT" BGCOLOR="#f6f9fb"><FONT POINT-SIZE="12">'+(c.pk?'PK ':'')+(fk?'FK ':'')+c.name+' : '+c.type+'</FONT></TD></TR>';}
  dot+=JSON.stringify(n)+' [label=<'+label+'</TABLE>>];\n';
 }
 for(const n of nodes)for(const f of schema[n].fk){
  if(!nodes.includes(f.table))continue;
  const col=schema[n].columns.find(c=>c.name===f.from);
  const optional=!col.notnull&&n!=='procedure_pricing';
  dot+=JSON.stringify(f.table)+' -> '+JSON.stringify(n)+' [label="'+f.from+'",dir=both,arrowtail="'+(optional?'odottee':'teetee')+'",arrowhead="'+(n==='procedure_pricing'?'teeodot':'crowodot')+'",taillabel="'+(optional?'0..1':'1')+'",headlabel="'+(n==='procedure_pricing'?'0..1':'0..N')+'",labeldistance=2];\n';
 }
 dot+='}';const svg=viz.renderString(dot,{format:'svg',engine:'dot'});
 await fs.writeFile(path.join(folder,name+'.dot'),dot);await fs.writeFile(path.join(folder,name+'.svg'),svg);
 await sharp(Buffer.from(svg),{density:160}).png().toFile(path.join(folder,name+'.png'));
}
console.log('Cinco ERD com relações e cardinalidades renderizados.');

