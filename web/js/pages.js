async function fetchText(url){ const r = await fetch(url); return r.text(); }
async function render(name, data={}){
  const tplSrc = await fetchText(`/app/templates/pages/${name}.hbs`);
  const tpl = Handlebars.compile(tplSrc);
  const html = tpl(data);
  const el = document.getElementById('content');
  if(el){ el.innerHTML = html; }
}
window.NutriPages = { render };