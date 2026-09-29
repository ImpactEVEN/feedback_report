'use strict';
const $ = id => document.getElementById(id);
let data;
const fmt = n => n === null || !Number.isFinite(n) ? '—' : n.toFixed(1);
const dateLabel = s => new Date(s + 'T12:00:00Z').toLocaleDateString('en-GB', {day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
function element(tag, text, className) {const e=document.createElement(tag); if(text!==undefined)e.textContent=text;if(className)e.className=className;return e;}
function metric(buckets,key){const counts=[0,0,0,0,0];for(const b of buckets){const c=b.metrics[key].counts;if(c)c.forEach((v,i)=>counts[i]+=v);}const n=counts.reduce((a,b)=>a+b,0);return {counts,n,avg:n?counts.reduce((s,v,i)=>s+v*(i+1),0)/n:null};}
function composite(buckets,key){let sum=0,n=0;for(const b of buckets){const c=b.composites[key];if(c.n){sum+=c.sum;n+=c.n;}}return {avg:n?sum/n:null,n};}
function selected(){const days=$('period').value;const cutoff=new Date(data.updated_at);if(days!=='all')cutoff.setUTCDate(cutoff.getUTCDate()-Number(days));const start=cutoff.toISOString().slice(0,10),end=data.updated_at.slice(0,10);return data.buckets.filter(b=>(!$('trip').value||b.date===$('trip').value)&&(days==='all'||(b.date>=start&&b.date<=end)));}
function bar(container,label,m){const row=element('div',undefined,'rating-row');row.append(element('span',label));const track=element('div',undefined,'track'),fill=element('div',undefined,'fill');fill.style.width=(m.avg===null?0:m.avg/5*100)+'%';track.append(fill);row.append(track);const value=element('span',fmt(m.avg),'rating-value');value.append(element('small','n = '+m.n));row.append(value);container.append(row);}
function render(){const bs=selected();$('responses').textContent=bs.reduce((s,b)=>s+b.responses,0);$('trips-count').textContent=bs.length+' published trips';for(const [key,id,nid] of [['support','support','support-n'],['trip','experience','trip-n']]){const c=composite(bs,key);$(id).textContent=fmt(c.avg)+(c.avg===null?'':' / 5');$(nid).textContent=c.n+' complete responses';}
let total=0,low=0;for(const k of Object.keys(data.fields)){const m=metric(bs,k);total+=m.n;low+=m.counts[0]+m.counts[1];}$('low').textContent=total?(100*low/total).toFixed(1)+'%':'—';
for(const [keys,id] of [[data.support_fields,'support-bars'],[data.trip_fields,'trip-bars']]){$(id).replaceChildren();keys.forEach(k=>bar($(id),data.fields[k],metric(bs,k)));}
const m=metric(bs,$('question').value);$('distribution').replaceChildren();for(let i=4;i>=0;i--){const row=element('div',undefined,'dist-row');row.append(element('span',(i+1)+' ★'));const track=element('div',undefined,'track'),fill=element('div',undefined,'fill');fill.style.width=(m.n?100*m.counts[i]/m.n:0)+'%';track.append(fill);row.append(track,element('span',m.n?Math.round(100*m.counts[i]/m.n)+'%':'—'));$('distribution').append(row);}$('distribution-n').textContent=m.n+' valid answers · '+fmt(m.avg)+' average';
$('attention').replaceChildren();let alerts=0;Object.keys(data.fields).map(k=>({k,...metric(bs,k)})).filter(m=>m.avg!==null&&m.avg<4).sort((a,b)=>a.avg-b.avg).forEach(m=>{alerts++;const row=element('div',undefined,'attention-item');row.append(element('strong',data.fields[m.k]+' · '+fmt(m.avg)+' / 5'),element('span',Math.round(100*(m.counts[0]+m.counts[1])/m.n)+'% low ratings · n = '+m.n));$('attention').append(row);});if(!alerts)$('attention').append(element('p',bs.length?'No published question averages below 4.0.':'No published results for these filters.','muted'));renderTrend(bs);renderComments();}
function renderTrend(bs){const key=$('trend-metric').value,months=[...new Set(bs.map(b=>b.date.slice(0,7)))].sort(),points=months.map(month=>({month,...composite(bs.filter(b=>b.date.startsWith(month)),key)})).filter(p=>p.avg!==null);$('trend').replaceChildren();if(!points.length){$('trend').append(element('p','No trend data for these filters.','muted'));return;}const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 460 210');svg.setAttribute('role','img');const title=document.createElementNS(ns,'title');title.textContent=points.map(p=>p.month+': '+fmt(p.avg)+' / 5, n = '+p.n).join('; ');svg.append(title);function shape(tag,attrs,text){const e=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;svg.append(e);return e;}for(let n=1;n<=5;n++){const y=170-(n-1)*35;shape('line',{x1:30,y1:y,x2:440,y2:y,stroke:'#e2eaf0'});shape('text',{x:8,y:y+5},String(n));}const x=i=>points.length===1?235:45+i*375/(points.length-1),y=p=>170-(p.avg-1)*35;shape('polyline',{points:points.map((p,i)=>x(i)+','+y(p)).join(' '),fill:'none',stroke:'#087f78','stroke-width':3});points.forEach((p,i)=>{shape('circle',{cx:x(i),cy:y(p),r:5,fill:'#087f78'});if(points.length<=6||i===0||i===points.length-1)shape('text',{x:x(i),y:198,'text-anchor':'middle'},p.month);});$('trend').append(svg);if(points.length===1)$('trend').append(element('p','One month available; more months are needed to assess a trend.','muted'));}
async function init(){try{const response=await fetch('data/dashboard.json',{cache:'no-store'});if(!response.ok)throw Error();data=await response.json();if(data.schema_version!==1||!Array.isArray(data.buckets))throw Error();$('updated').textContent='Updated '+new Date(data.updated_at).toLocaleString('en-GB',{dateStyle:'medium',timeStyle:'short'});const notices=[];if(data.demo)notices.push('DEMO · Fictional responses for design preview. These are not NGO results.');if(data.withheld_responses)notices.push(data.withheld_responses+' responses withheld because their trips have fewer than '+data.minimum_group_size+' responses.');if(data.invalid_date_responses)notices.push(data.invalid_date_responses+' responses excluded because the trip date is missing or invalid.');if(!data.buckets.length)notices.push('No trips currently meet the publication threshold.');$('notice').textContent=notices.join(' ');for(const b of data.buckets){const o=element('option',dateLabel(b.date));o.value=b.date;$('trip').append(o);}for(const [k,label]of Object.entries(data.fields)){const o=element('option',label);o.value=k;$('question').append(o);}for(const id of ['trip','period','question','trend-metric'])$(id).addEventListener('change',render);$('reset').addEventListener('click',()=>{$('trip').value='';$('period').value='all';render();});render();}catch{$('notice').textContent='The dashboard data could not be loaded. Please try again later.';$('updated').textContent='Update unavailable';for(const id of ['trip','period','question','trend-metric','reset'])$(id).disabled=true;}}
init();

const commentQuestions = {
 pre_feedback: {label:'Before the trip',question:'¿Tienes alguna recomendación para el equipo encargado de la preparación de los voluntarios a viajar?'},
 feedback: {label:'Weekly Canaima team',question:'¿Tienes alguna recomendación para el equipo recurrente en Weekly Canaima?'},
 apoyo: {label:'Next volunteers',question:'¿Tienes alguna recomendación para el siguiente grupo de voluntarios a viajar?'},
 header_3: {label:'Additional recommendations',question:'¿Tienes alguna recomendación adicional?'}
};
const fictionalComments = [
 {category:'pre_feedback',text:'Sería útil recibir una lista de lo que debemos llevar y el itinerario unos días antes del viaje.'},
 {category:'pre_feedback',text:'Los materiales de preparación fueron útiles. Una breve reunión para resolver dudas antes de salir ayudaría mucho.'},
 {category:'feedback',text:'Me sentí acompañado por el equipo. Podríamos acordar un momento al final del día para compartir lo que funcionó y lo que necesitamos ajustar.'},
 {category:'feedback',text:'Ayudaría confirmar con la posada los horarios de las comidas para organizar mejor las actividades.'},
 {category:'apoyo',text:'Lleven los materiales organizados por actividad y revisen juntos el plan del primer día antes de viajar.'},
 {category:'header_3',text:'Sería bueno compartir después del viaje un resumen de las recomendaciones y de las mejoras que se van implementando.'}
];
let activeCommentCategory='all';
function renderComments(category=activeCommentCategory) {
 activeCommentCategory=category;
 $('voices-section').hidden=false;
 $('comment-question').textContent=category==='all'?'Recommendations for preparation, the recurring team, future volunteers and other improvements.':commentQuestions[category].question;
 $('comments').replaceChildren();
 const comments=data.demo?fictionalComments:selected().flatMap(b=>(b.comments||[]).map(c=>({...c,date:b.date})));
 $('comments-status').textContent=data.demo?'Fictional preview examples':'Volunteer recommendations';
 $('comments-description').textContent=data.demo?'Fictional examples for the four open questions. These examples are independent of the trip filters.':'Open answers for the selected trips and period. Names are not displayed; comments are shown as submitted.';
 for(const c of comments.filter(c=>category==='all'||c.category===category)) {
  const card=element('article',undefined,'comment-card');
  card.append(element('h3',commentQuestions[c.category].label));
  const quote=element('blockquote',c.text);quote.lang='es';card.append(quote,element('small',data.demo?'Fictional example · not a submitted response':'Trip: '+dateLabel(c.date)));
  $('comments').append(card);
 }
 if(!$('comments').children.length)$('comments').append(element('p','No comments for these filters.','muted'));
 for(const b of document.querySelectorAll('[data-category]')){b.setAttribute('aria-pressed',String(b.dataset.category===category));b.onclick=()=>renderComments(b.dataset.category);}
}
