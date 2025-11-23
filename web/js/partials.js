async function fetchText(url){ const r = await fetch(url); return r.text(); }
async function registerPartials(){
  const base = '/app/templates/partials';
  const files = ['header','footer','targets','totals'];
  for(const f of files){
    const tpl = await fetchText(`${base}/${f}.hbs`);
    Handlebars.registerPartial(f, tpl);
  }
}

async function renderShell(){
  await registerPartials();
  const header = Handlebars.compile('{{> header}}')({});
  const footer = Handlebars.compile('{{> footer}}')({});
  const h = document.getElementById('header'); if(h) h.innerHTML = header;
  const f = document.getElementById('footer'); if(f) f.innerHTML = footer;
  // theme
  const toggle = document.getElementById('themeToggle');
  if(toggle){ toggle.addEventListener('click', toggleTheme); }
  applySavedTheme();
}

function applySavedTheme(){
  const mode = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', mode);
}

function toggleTheme(){
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

window.NutriPartials = { renderShell };
