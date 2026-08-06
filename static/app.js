/* SEHAT frontend */
(function () {
  "use strict";

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  const api = async (path, opts) => {
    const res = await fetch(path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data && data.detail
        ? (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(" ") : String(data.detail))
        : "Something went wrong. Please try again.";
      throw new Error(msg);
    }
    return data;
  };

  /* ------------------------------------------------------------ state */

  const state = { sex: "", session: null, stage: "intake", faList: [] };

  /* ------------------------------------------------------- navigation */

  const views = { home: $("#view-home"), consult: $("#view-consult"), firstaid: $("#view-firstaid") };

  function show(view) {
    Object.entries(views).forEach(([k, el]) => el.classList.toggle("hidden", k !== view));
    window.scrollTo({ top: 0 });
    if (view === "firstaid" && !state.faList.length) loadFirstAid();
  }

  document.addEventListener("click", (e) => {
    const nav = e.target.closest("[data-nav]");
    if (nav) { e.preventDefault(); show(nav.dataset.nav); }
  });

  /* ----------------------------------------------------------- health */

  api("/api/health").then((h) => {
    if (!h.ai_configured) $("#demo-banner").classList.remove("hidden");
  }).catch(() => {});

  /* ----------------------------------------------------------- intake */

  const pregRow = $("#preg-row");
  const pregWeeks = $("#preg-weeks");
  const weeksInput = $("#f-weeks");
  const trimChip = $("#trimester-chip");

  $$("#f-sex button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.sex = btn.dataset.val;
      $$("#f-sex button").forEach((b) => b.classList.toggle("on", b === btn));
      pregRow.classList.toggle("hidden", state.sex !== "female");
      if (state.sex !== "female") {
        $("#f-pregnant").checked = false;
        pregWeeks.classList.add("hidden");
      }
    });
  });

  $("#f-pregnant").addEventListener("change", (e) => {
    pregWeeks.classList.toggle("hidden", !e.target.checked);
    if (e.target.checked) weeksInput.focus();
  });

  weeksInput.addEventListener("input", () => {
    const w = parseInt(weeksInput.value, 10);
    if (w >= 1 && w <= 45) {
      const t = w <= 12 ? "1st trimester" : w <= 27 ? "2nd trimester" : "3rd trimester";
      trimChip.textContent = w + " weeks · " + t;
      trimChip.classList.remove("hidden");
    } else {
      trimChip.classList.add("hidden");
    }
  });

  $("#intake-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = $("#intake-error");
    err.classList.add("hidden");

    const pregnant = $("#f-pregnant").checked;
    const body = {
      age: parseInt($("#f-age").value, 10),
      sex: state.sex,
      pregnant,
      pregnancy_weeks: pregnant ? parseInt(weeksInput.value, 10) || null : null,
      complaint: $("#f-complaint").value.trim(),
      duration: $("#f-duration").value,
      conditions: $("#f-conditions").value.trim(),
    };

    if (!body.sex) return fail("Please select sex — it changes the medical picture.");
    if (pregnant && !body.pregnancy_weeks)
      return fail("Please enter how many weeks pregnant — this decides what is safe and what is urgent.");

    const btn = $("#start-btn");
    btn.disabled = true; btn.textContent = "Starting…";
    try {
      const res = await api("/api/consult/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      $("#intake").classList.add("hidden");
      $("#chat").classList.remove("hidden");
      addUserBubble(body.complaint);
      handle(res);
    } catch (ex) {
      fail(ex.message);
    } finally {
      btn.disabled = false; btn.textContent = "Begin consultation";
    }

    function fail(msg) { err.textContent = msg; err.classList.remove("hidden"); }
  });

  /* ------------------------------------------------------------- chat */

  const chat = $("#chat");
  const composer = $("#composer");
  const quickBox = $("#quick-options");
  const answerInput = $("#answer-input");

  function scrollChat() { window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }); }

  function addUserBubble(text) {
    chat.insertAdjacentHTML("beforeend",
      '<div class="bubble bubble-user">' + esc(text) + "</div>");
    scrollChat();
  }

  function addThinking() {
    chat.insertAdjacentHTML("beforeend",
      '<div class="bubble bubble-doc" id="thinking"><div class="doc-name">SEHAT · Doctor</div>' +
      '<span class="thinking"><i></i><i></i><i></i></span></div>');
    scrollChat();
  }
  const removeThinking = () => { const t = $("#thinking"); if (t) t.remove(); };

  async function send(text) {
    if (!state.session) return;
    addUserBubble(text);
    quickBox.innerHTML = "";
    answerInput.value = "";
    composer.classList.add("hidden");
    addThinking();
    try {
      const res = await api("/api/consult/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: state.session, answer: text }),
      });
      removeThinking();
      handle(res);
    } catch (ex) {
      removeThinking();
      renderError(ex.message);
    }
  }

  $("#answer-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const text = answerInput.value.trim();
    if (text) send(text);
  });

  /* --------------------------------------------------------- handlers */

  function handle(res) {
    if (res.session_id) state.session = res.session_id;
    switch (res.type) {
      case "question": return renderQuestion(res);
      case "assessment": return renderAssessment(res.assessment);
      case "emergency": return renderEmergency(res);
      case "crisis": return renderCrisis(res);
      case "guard": return renderGuard(res);
      case "followup": return renderFollowup(res);
      default: return renderError(res.message || "Unexpected reply.");
    }
  }

  function renderQuestion(res) {
    const prog = res.progress
      ? '<div class="progress">Question ' + res.progress.asked + " of " + res.progress.max + "</div>"
      : "";
    const why = res.why_asking
      ? '<div class="why">Why I\u2019m asking: ' + esc(res.why_asking) + "</div>"
      : "";
    chat.insertAdjacentHTML("beforeend",
      '<div class="bubble bubble-doc"><div class="doc-name">SEHAT · Doctor</div>' +
      "<div>" + esc(res.question) + "</div>" + why + prog + "</div>");

    quickBox.innerHTML = (res.quick_options || [])
      .map((o) => "<button type=\"button\">" + esc(o) + "</button>").join("");
    $$("button", quickBox).forEach((b) => b.addEventListener("click", () => send(b.textContent)));
    composer.classList.remove("hidden");
    answerInput.focus();
    scrollChat();
  }

  function renderFollowup(res) {
    chat.insertAdjacentHTML("beforeend",
      '<div class="bubble bubble-doc"><div class="doc-name">SEHAT · Doctor</div><div>' +
      esc(res.answer).replace(/\n/g, "<br>") + "</div></div>");
    composer.classList.remove("hidden");
    answerInput.placeholder = "Ask a follow-up about your assessment…";
    scrollChat();
  }

  function renderGuard(res) {
    chat.insertAdjacentHTML("beforeend",
      '<div class="guard">' + esc(res.message) + "</div>");
    composer.classList.remove("hidden");
    scrollChat();
  }

  function renderError(msg) {
    chat.insertAdjacentHTML("beforeend",
      '<div class="guard">' + esc(msg) + "</div>");
    composer.classList.remove("hidden");
    scrollChat();
  }

  /* ------------------------------------------------------- emergency */

  function protocolHTML(p) {
    const steps = (p.steps || []).map((s) => "<li>" + esc(s) + "</li>").join("");
    const donot = (p.do_not || []).map((s) => "<li>" + esc(s) + "</li>").join("");
    const until = (p.until_hospital || []).map((s) => "<li>" + esc(s) + "</li>").join("");
    return (
      '<div class="emg-body">' +
      '<ol class="emg-steps">' + steps + "</ol>" +
      (donot ? '<div class="emg-block emg-donot"><h4>Never do this</h4><ul>' + donot + "</ul></div>" : "") +
      (until ? '<div class="emg-block emg-until"><h4>Until you reach the hospital</h4><ul>' + until + "</ul></div>" : "") +
      "</div>"
    );
  }

  function renderEmergency(res) {
    composer.classList.add("hidden");
    const p = res.protocol || {};
    chat.insertAdjacentHTML("beforeend",
      '<div class="emg">' +
      '<div class="emg-head"><h3>🚨 ' + esc(res.label || "Medical emergency") + "</h3>" +
      (res.reason ? "<p>" + esc(res.reason) + "</p>" : "") +
      "<p>This needs a hospital — not an app. Start these steps while help is on the way.</p></div>" +
      '<div class="emg-call">' +
      '<a class="btn btn-danger" href="tel:' + esc(res.call || "1122") + '">📞 Call ' + esc(res.call || "1122") + " — Rescue</a>" +
      '<a class="btn btn-ghost" href="tel:115">Edhi — 115</a>' +
      "</div>" +
      '<div style="padding:0 20px 6px"><b>' + esc(p.title || "") + "</b> <span class=\"muted\">" + esc(p.signs || "") + "</span></div>" +
      protocolHTML(p) +
      "</div>");
    scrollChat();
  }

  function renderCrisis(res) {
    composer.classList.add("hidden");
    const lines = (res.helplines || []).map((h) =>
      '<a href="tel:' + esc(h.number.replace(/[^0-9+]/g, "")) + '"><span>' + esc(h.name) +
      "</span><span>" + esc(h.number) + "</span></a>").join("");
    chat.insertAdjacentHTML("beforeend",
      '<div class="crisis"><h3>You matter. Please reach out.</h3><p>' + esc(res.message) + "</p>" +
      '<div class="helplines">' + lines + "</div>" +
      "<p class=\"muted\">" + esc(res.note || "") + "</p></div>");
    scrollChat();
  }

  /* ------------------------------------------------------ assessment */

  const URGENCY_LABELS = {
    within_24_hours: "See a doctor within 24 hours",
    within_3_days: "See a doctor within 3 days",
    this_week: "See a doctor this week",
    routine: "Routine visit when convenient",
  };
  const BADGES = { "most likely": "badge-most", possible: "badge-poss", "less likely": "badge-less" };

  function renderAssessment(a) {
    const conds = (a.possible_conditions || []).map((c) => {
      const cls = BADGES[(c.likelihood || "").toLowerCase()] || "badge-poss";
      return '<div class="cond"><div class="cond-top"><span class="cond-name">' + esc(c.name) +
        '</span><span class="badge ' + cls + '">' + esc(c.likelihood || "possible") + "</span></div>" +
        (c.why ? '<div class="cond-why">' + esc(c.why) + "</div>" : "") +
        (c.specialist ? '<div class="cond-spec">Treated by: ' + esc(c.specialist) + "</div>" : "") +
        "</div>";
    }).join("");

    const list = (items) => (items || []).map((i) => "<li>" + esc(i) + "</li>").join("");

    const otcHTML = (a.otc || []).map((o) =>
      '<div class="otc-item"><div class="otc-name">' + esc(o.name) + "</div>" +
      '<div class="otc-dose">' + esc(o.adult) + "</div>" +
      (o.note ? '<div class="otc-note">' + esc(o.note) + "</div>" : "") +
      (o.preg_note ? '<div class="otc-note">Pregnancy: ' + esc(o.preg_note) + "</div>" : "") +
      '<div class="otc-note">Caution: ' + esc(o.cautions) + "</div></div>").join("");

    const sd = a.see_doctor || {};
    const qs = (a.questions_for_your_doctor || []).map((q) => "<li>" + esc(q) + "</li>").join("");
    const today = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

    chat.insertAdjacentHTML("beforeend",
      '<div class="rx">' +
      '<div class="rx-head"><div class="rx-brand">✚ SEHAT <span>· clinical summary</span></div>' +
      '<div class="rx-patient"><span>' + esc(a.patient_line || "") + "</span><span>" + today + "</span></div></div>" +
      '<div class="rx-body">' +
      (a.demo_note ? '<div class="demo-note">' + esc(a.demo_note) + "</div>" : "") +
      '<div class="rx-sec"><h4>Case summary</h4><p>' + esc(a.case_summary || "") + "</p></div>" +
      (conds ? '<div class="rx-sec"><h4>What this may be</h4>' + conds + "</div>" : "") +
      ((a.red_flags || []).length
        ? '<div class="rx-sec rx-red"><h4>Go to a hospital immediately if</h4><ul>' + list(a.red_flags) + "</ul></div>" : "") +
      ((a.precautions || []).length
        ? '<div class="rx-sec"><h4>Precautions</h4><ul>' + list(a.precautions) + "</ul></div>" : "") +
      ((a.self_care || []).length
        ? '<div class="rx-sec"><h4>Safe self-care</h4><ul>' + list(a.self_care) + "</ul></div>" : "") +
      (otcHTML ? '<div class="rx-sec rx-otc"><h4>Pharmacy (over-the-counter only)</h4>' + otcHTML + "</div>" : "") +
      (a.pregnancy_note
        ? '<div class="rx-sec rx-preg"><h4>Because you are pregnant</h4><p>' + esc(a.pregnancy_note) + "</p></div>" : "") +
      '<div class="rx-doctor"><span class="urgency">' + esc(URGENCY_LABELS[sd.urgency] || URGENCY_LABELS.within_3_days) +
      '</span><span class="who">' + esc(sd.who || "General Physician") + "</span>" +
      (sd.why ? '<span class="why-doc">' + esc(sd.why) + "</span>" : "") + "</div>" +
      "</div>" +
      (qs ? '<div class="rx-tear"><h4>Bring this to your doctor — questions to ask</h4><ol>' + qs + "</ol></div>" : "") +
      '<div class="rx-disclaimer">' + esc(a.disclaimer || "") + "</div>" +
      '<div class="rx-actions"><button class="btn btn-ghost" onclick="window.print()">🖨 Print / save</button>' +
      '<button class="btn btn-ghost" onclick="location.reload()">New consultation</button></div>' +
      "</div>");

    composer.classList.remove("hidden");
    answerInput.placeholder = "Ask a follow-up about your assessment…";
    scrollChat();
  }

  /* ------------------------------------------------------- first aid */

  async function loadFirstAid() {
    try {
      const data = await api("/api/firstaid");
      state.faList = data.protocols || [];
      renderFaGrid(state.faList);
    } catch (ex) {
      $("#fa-grid").innerHTML = '<p class="muted">Could not load first aid. ' + esc(ex.message) + "</p>";
    }
  }

  function renderFaGrid(items) {
    $("#fa-grid").innerHTML = items.map((p) =>
      '<button class="fa-card" data-pid="' + esc(p.id) + '">' +
      '<span class="fa-icon">' + esc(p.icon) + "</span>" +
      "<h3>" + esc(p.title) + "</h3><p>" + esc(p.signs) + "</p></button>").join("") ||
      '<p class="muted">No match — try another word, or call 1122 if it\u2019s urgent.</p>';
    $$(".fa-card").forEach((c) => c.addEventListener("click", () => openProtocol(c.dataset.pid)));
  }

  $("#fa-search").addEventListener("input", (e) => {
    const q = e.target.value.trim().toLowerCase();
    renderFaGrid(!q ? state.faList : state.faList.filter((p) =>
      (p.title + " " + p.signs + " " + p.id).toLowerCase().includes(q)));
    $("#fa-detail").classList.add("hidden");
    $("#fa-grid").classList.remove("hidden");
  });

  async function openProtocol(pid) {
    try {
      const p = await api("/api/firstaid/" + encodeURIComponent(pid));
      $("#fa-grid").classList.add("hidden");
      $("#fa-detail").classList.remove("hidden");
      $("#fa-detail").innerHTML =
        '<button class="btn btn-ghost fa-back" id="fa-back">← All first aid</button>' +
        '<div class="emg"><div class="emg-head"><h3>' + esc(p.icon) + " " + esc(p.title) + "</h3>" +
        "<p>" + esc(p.signs) + "</p></div>" +
        '<div class="emg-call"><a class="btn btn-danger" href="tel:' + esc(p.call) + '">📞 Call ' + esc(p.call) +
        ' — Rescue</a><a class="btn btn-ghost" href="tel:115">Edhi — 115</a></div>' +
        protocolHTML(p) + "</div>";
      $("#fa-back").addEventListener("click", () => {
        $("#fa-detail").classList.add("hidden");
        $("#fa-grid").classList.remove("hidden");
      });
      window.scrollTo({ top: 0 });
    } catch (ex) { /* stay on grid */ }
  }

})();
