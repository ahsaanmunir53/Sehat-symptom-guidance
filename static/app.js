/* SEHAT — front end. No framework on purpose: zero build step means zero
   dependency breakage, and it deploys as static files next to the API. */

const REGIONS = [
  { id: 'head',    label: 'Head',     cx: 50, cy: 10, r: 7.6, say: 'a headache' },
  { id: 'throat',  label: 'Throat',   cx: 50, cy: 20, r: 4.4, say: 'a sore throat' },
  { id: 'chest',   label: 'Chest',    cx: 50, cy: 32, r: 7.8, say: 'discomfort in my chest' },
  { id: 'stomach', label: 'Stomach',  cx: 50, cy: 46, r: 7.8, say: 'stomach pain' },
  { id: 'back',    label: 'Back',     cx: 68, cy: 40, r: 6.0, say: 'back pain' },
  { id: 'arm',     label: 'Arms',     cx: 31, cy: 38, r: 5.4, say: 'pain in my arm' },
  { id: 'legs',    label: 'Legs',     cx: 45, cy: 74, r: 6.4, say: 'leg pain' },
  { id: 'skin',    label: 'Skin',     cx: 68, cy: 62, r: 5.6, say: 'a skin rash' },
];
const DURATIONS = ['Today', '2–3 days', 'About a week', 'Over 2 weeks', 'Months'];
const CONDITIONS = ['Pregnant', 'Diabetes', 'High blood pressure', 'Asthma', 'Kidney problem', 'Heart condition'];
const LOADING_MSGS = [
  'Reading what you wrote…',
  'Running safety checks…',
  'Putting the guidance together…',
];

const state = { regions: [], duration: '', conditions: [], step: 1 };
const $ = (id) => document.getElementById(id);

/* ---------- setup ---------- */
function buildChips(hostId, items, key) {
  const host = $(hostId);
  host.innerHTML = '';
  items.forEach((t) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'chip'; b.textContent = t;
    b.onclick = () => {
      if (key === 'duration') {
        state.duration = state.duration === t ? '' : t;
        [...host.children].forEach((c) => c.classList.toggle('on', c.textContent === state.duration));
      } else {
        const i = state.conditions.indexOf(t);
        i > -1 ? state.conditions.splice(i, 1) : state.conditions.push(t);
        b.classList.toggle('on');
      }
    };
    host.appendChild(b);
  });
}

function buildBody() {
  const svg = $('hotspots');
  const list = $('regionList');
  svg.innerHTML = ''; list.innerHTML = '';
  REGIONS.forEach((r) => {
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'hot'); g.dataset.id = r.id;
    const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    c.setAttribute('cx', r.cx); c.setAttribute('cy', r.cy); c.setAttribute('r', r.r);
    g.appendChild(c); g.onclick = () => toggleRegion(r); svg.appendChild(g);

    const b = document.createElement('button');
    b.type = 'button'; b.className = 'chip'; b.textContent = r.label;
    b.dataset.id = r.id; b.onclick = () => toggleRegion(r);
    list.appendChild(b);
  });
}

function toggleRegion(r) {
  const i = state.regions.indexOf(r.id);
  const ta = $('symptoms');
  if (i > -1) {
    state.regions.splice(i, 1);
  } else {
    state.regions.push(r.id);
    const cur = ta.value.trim();
    ta.value = cur ? `${cur}, ${r.say}` : `I have ${r.say}`;
  }
  document.querySelectorAll(`.hot[data-id="${r.id}"]`).forEach((e) => e.classList.toggle('on'));
  document.querySelectorAll(`#regionList .chip[data-id="${r.id}"]`).forEach((e) => e.classList.toggle('on'));
}

/* ---------- navigation ---------- */
function start() {
  $('hero').classList.add('hidden');
  $('wizard').classList.remove('hidden');
  $('wizard').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function go(n) {
  if (n === 2 && !$('age').value) { flash('Please enter your age first.'); return; }
  state.step = n;
  document.querySelectorAll('.step-panel').forEach((p) => p.classList.toggle('on', +p.dataset.panel === n));
  document.querySelectorAll('.step').forEach((s) => {
    const v = +s.dataset.s;
    s.classList.toggle('on', v === n);
    s.classList.toggle('done', v < n);
  });
  $('wizard').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function flash(msg) {
  const e = $('err');
  e.textContent = msg; e.classList.remove('hidden');
  setTimeout(() => e.classList.add('hidden'), 4500);
}

/* ---------- submit ---------- */
async function submitForm(ev) {
  ev.preventDefault();
  const age = parseInt($('age').value, 10);
  const symptoms = $('symptoms').value.trim();
  if (!age || age < 1 || age > 119) { flash('Enter an age between 1 and 119.'); go(1); return; }
  if (symptoms.length < 8) { flash('Please describe how you feel in a sentence or two.'); return; }

  $('wizard').classList.add('hidden');
  $('result').classList.add('hidden');
  $('loading').classList.remove('hidden');

  let i = 0;
  const tick = setInterval(() => {
    i = (i + 1) % LOADING_MSGS.length;
    $('loadMsg').textContent = LOADING_MSGS[i];
  }, 1900);

  try {
    const res = await fetch('/api/triage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        age, sex: $('sex').value, duration: state.duration,
        symptoms, conditions: state.conditions,
      }),
    });
    const data = await res.json();
    clearInterval(tick);
    $('loading').classList.add('hidden');
    if (!res.ok) {
      $('wizard').classList.remove('hidden');
      flash(data.detail || 'The guidance service is unavailable. Please try again.');
      go(3);
      return;
    }
    render(data);
  } catch (e) {
    clearInterval(tick);
    $('loading').classList.add('hidden');
    $('wizard').classList.remove('hidden');
    flash('Could not reach the service. Check your connection and try again.');
    go(3);
  }
}

/* ---------- rendering ---------- */
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const li = (arr) => (arr || []).map((x) => `<li>${esc(x)}</li>`).join('');

function render(d) {
  const R = $('result');
  R.classList.remove('hidden');

  if (d.band === 'emergency' || d.band === 'crisis') {
    const crisis = d.band === 'crisis';
    R.innerHTML = `
      <div class="verdict ${crisis ? 'crisis' : 'emergency'}">
        <div class="vicon">${crisis ? '♥' : '!'}</div>
        <h2>${esc(d.headline)}</h2>
        <p class="vmsg">${esc(d.message)}</p>
        <ul class="vlist">${li(d.actions)}</ul>
        <p class="disc">${esc(d.note)}</p>
        <button class="again" onclick="location.reload()">Start over</button>
      </div>`;
    R.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }

  const sevLabel = { mild: 'Likely mild', moderate: 'Worth watching', see_doctor_soon: 'See a doctor soon' };
  const sev = d.severity || 'moderate';

  const causes = (d.possible_causes || []).map((c, i) => `
    <article class="cause" style="animation-delay:${i * 0.08}s">
      <div class="cause-h">
        <h4>${esc(c.name)}</h4>
        <span class="lk ${esc(String(c.likelihood || '').replace(/\s+/g, '-'))}">${esc(c.likelihood)}</span>
      </div>
      <p>${esc(c.why)}</p>
    </article>`).join('');

  const pharm = (d.pharmacy || []).map((p) => `
    <div class="pharm">
      <div class="pharm-h">
        <h4>${esc(p.category)}</h4>
        <span class="pharm-name">${esc(p.common_names)}</span>
      </div>
      <p>${esc(p.what_it_does)}</p>
      ${p.who_must_not && p.who_must_not.length ? `
        <div class="nono">
          <strong>Do not take this if</strong>
          <ul style="margin:0;padding-left:1.1rem">${li(p.who_must_not)}</ul>
        </div>` : ''}
      <p class="askrx">→ <span>${esc(p.ask_pharmacist)}</span></p>
    </div>`).join('');

  R.innerHTML = `
    <div class="block">
      <span class="sev ${esc(sev)}">${esc(sevLabel[sev] || 'Guidance')}</span>
      <p class="summary">${esc(d.summary)}</p>
      ${d.expected_course ? `<p class="note" style="margin-top:1rem">${esc(d.expected_course)}</p>` : ''}
    </div>

    ${(d.age_notes || []).length ? `<div class="agebox">${(d.age_notes).map((n) => `<p>${esc(n)}</p>`).join('')}</div>` : ''}

    <div class="block">
      <h3>What this could be</h3>
      <p class="note">Possibilities to discuss with a doctor — not a diagnosis.</p>
      <div class="causes">${causes}</div>
    </div>

    <div class="two">
      <div class="block"><h3>What helps</h3><ul class="mark do">${li(d.self_care)}</ul></div>
      <div class="block"><h3>What to avoid</h3><ul class="mark dont">${li(d.avoid)}</ul></div>
    </div>

    <div class="block flags">
      <h3>See a doctor sooner if…</h3>
      <ul class="mark warn">${li(d.red_flags)}</ul>
    </div>

    ${pharm ? `
      <div class="block">
        <h3>At the pharmacy counter</h3>
        <p class="note">General categories only. Your pharmacist is free to consult and needs no appointment.</p>
        ${pharm}
        <div class="dose">
          <strong>Why no dose is shown</strong>
          <p>${esc(d.dose_notice)}</p>
        </div>
      </div>` : ''}

    <p class="disc">${esc(d.disclaimer)}</p>
    <button class="again" onclick="location.reload()">Check something else</button>`;

  R.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ---------- boot ---------- */
buildChips('durations', DURATIONS, 'duration');
buildChips('conds', CONDITIONS, 'conditions');
buildBody();
