const state = {
  rawData: null,
  currentScenario: "base",
  cashflowChart: null,
  comparisonChart: null
};

const SCENARIO_TITLES = {
  base: "Базовый",
  optimistic: "Оптимистичный",
  pessimistic: "Пессимистичный"
};

const metricNodes = {
  npv: document.getElementById("npvValue"),
  irr: document.getElementById("irrValue"),
  pi: document.getElementById("piValue"),
  pp: document.getElementById("ppValue")
};

const analysisForm = document.getElementById("analysisForm");
const scenarioButtonsContainer = document.getElementById("scenarioButtons");
const themeToggle = document.getElementById("themeToggle");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");
const apiError = document.getElementById("apiError");

const NUMERIC_IDS = [
  "planning_years",
  "startup_capital",
  "discount_rate",
  "tax_rate_usn_dr",
  "patent_cost",
  "monthly_customers_start",
  "customers_growth_monthly",
  "average_check",
  "additional_income_monthly",
  "cost_per_client_monthly",
  "employees_count",
  "avg_salary",
  "benefit_employees_count",
  "insurance_benefit_rate",
  "insurance_rate_standard",
  "rent_monthly",
  "utilities_monthly",
  "office_expenses_monthly",
  "marketing_budget_monthly",
  "other_fixed_expenses_monthly"
];

function formatMoney(value, currency = "RUB") {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency,
    maximumFractionDigits: 0
  }).format(value);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

function formatYears(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "не достигнута";
  return `${Number(value).toFixed(2)} г.`;
}

function setFieldError(inputNode, message) {
  const field = inputNode.closest(".field");
  if (!field) return;
  field.classList.add("invalid");
  const error = field.querySelector(".error-text");
  if (error) error.textContent = message;
}

function clearFieldError(inputNode) {
  const field = inputNode.closest(".field");
  if (!field) return;
  field.classList.remove("invalid");
  const error = field.querySelector(".error-text");
  if (error) error.textContent = "";
}

function clearAllFieldErrors() {
  analysisForm.querySelectorAll(".field.invalid").forEach((f) => f.classList.remove("invalid"));
  analysisForm.querySelectorAll(".error-text").forEach((e) => {
    e.textContent = "";
  });
}

function parseAndValidateForm() {
  clearAllFieldErrors();
  let isValid = true;

  const projectName = document.getElementById("project_name");
  if (!projectName.value.trim()) {
    setFieldError(projectName, "Укажите название");
    isValid = false;
  }

  for (const id of NUMERIC_IDS) {
    const node = document.getElementById(id);
    if (!node) continue;
    const raw = node.value.trim();
    if (raw === "") {
      setFieldError(node, "Обязательное поле");
      isValid = false;
      continue;
    }
    const value = Number(raw);
    if (!Number.isFinite(value)) {
      setFieldError(node, "Введите число");
      isValid = false;
      continue;
    }
    if (value < 0 && id !== "customers_growth_monthly") {
      setFieldError(node, "Отрицательное значение недопустимо");
      isValid = false;
    }
    if (id === "planning_years" && (!Number.isInteger(value) || value < 1)) {
      setFieldError(node, "Целое число лет ≥ 1");
      isValid = false;
    }
    if (id === "tax_rate_usn_dr" && value > 100) {
      setFieldError(node, "0–100%");
      isValid = false;
    }
  }

  return isValid;
}

function buildPayloadFromForm() {
  const num = (id) => Number(document.getElementById(id).value);
  return {
    project_name: document.getElementById("project_name").value.trim() || "Проект",
    planning_years: Math.round(num("planning_years")),
    startup_capital: num("startup_capital"),
    business_type: document.getElementById("business_type").value,
    tax_mode: document.getElementById("tax_mode").value,
    income_source: document.getElementById("income_source").value,
    monthly_customers_start: Math.round(num("monthly_customers_start")),
    customers_growth_monthly: num("customers_growth_monthly"),
    average_check: num("average_check"),
    additional_income_monthly: num("additional_income_monthly"),
    employees_count: Math.round(num("employees_count")),
    avg_salary: num("avg_salary"),
    has_benefit_employees: document.getElementById("has_benefit_employees").checked,
    benefit_employees_count: Math.round(num("benefit_employees_count")),
    insurance_benefit_rate: num("insurance_benefit_rate"),
    rent_monthly: num("rent_monthly"),
    utilities_monthly: num("utilities_monthly"),
    office_expenses_monthly: num("office_expenses_monthly"),
    marketing_budget_monthly: num("marketing_budget_monthly"),
    cost_per_client_monthly: num("cost_per_client_monthly"),
    other_fixed_expenses_monthly: num("other_fixed_expenses_monthly"),
    tax_system: document.getElementById("tax_system").value,
    tax_rate_usn_dr: num("tax_rate_usn_dr"),
    has_vat: document.getElementById("has_vat").checked,
    insurance_rate_standard: num("insurance_rate_standard"),
    patent_cost: num("patent_cost"),
    discount_rate: num("discount_rate")
  };
}

function fillFormFromPayload(data) {
  if (!data || typeof data !== "object") return;
  if (data.project_name != null) document.getElementById("project_name").value = String(data.project_name);
  for (const id of NUMERIC_IDS) {
    if (Object.hasOwn(data, id)) {
      const el = document.getElementById(id);
      if (el) el.value = data[id];
    }
  }
  const selects = ["business_type", "tax_mode", "income_source", "tax_system"];
  for (const id of selects) {
    if (Object.hasOwn(data, id)) {
      const el = document.getElementById(id);
      if (el) el.value = data[id];
    }
  }
  if (typeof data.has_benefit_employees === "boolean") {
    document.getElementById("has_benefit_employees").checked = data.has_benefit_employees;
  }
  if (typeof data.has_vat === "boolean") {
    document.getElementById("has_vat").checked = data.has_vat;
  }
}

/** Преобразует ответ API в структуру для графиков */
function normalizeApiResult(apiResult) {
  const scenarios = apiResult.scenarios || {};
  const keys = ["base", "optimistic", "pessimistic"];
  const firstKey = keys.find((k) => scenarios[k]) || Object.keys(scenarios)[0];
  const yearsLen = scenarios[firstKey]?.cashflow?.length || 1;
  const startYear = new Date().getFullYear();
  const years = Array.from({ length: yearsLen }, (_, i) => String(startYear + i));

  const out = {
    currency: "RUB",
    years,
    scenarios: {}
  };

  for (const key of keys) {
    const s = scenarios[key];
    if (!s) continue;
    out.scenarios[key] = {
      title: SCENARIO_TITLES[key] || key,
      metrics: {
        NPV: s.npv,
        IRR: s.irr,
        PI: s.pi,
        PP: s.pp
      },
      cashflow: s.cashflow || []
    };
  }
  return out;
}

function radarNormalizedData(scenarios) {
  const keys = Object.keys(scenarios);
  const labels = ["NPV (отн.)", "IRR % (отн.)", "PI (отн.)", "Окупаемость (отн.)"];
  const ppScore = (pp) => {
    if (pp == null || pp <= 0) return 0;
    return Math.min(1, 5 / pp);
  };
  const raw = keys.map((k) => {
    const m = scenarios[k].metrics;
    return [m.NPV, m.IRR * 100, m.PI, ppScore(m.PP)];
  });
  const dims = 4;
  const norm = keys.map(() => Array(dims).fill(0));
  for (let d = 0; d < dims; d += 1) {
    const col = raw.map((r) => r[d]);
    const lo = Math.min(...col);
    const hi = Math.max(...col);
    const span = hi - lo || 1;
    for (let i = 0; i < keys.length; i += 1) {
      norm[i][d] = (raw[i][d] - lo) / span;
    }
  }
  return { keys, labels, norm };
}

function renderScenarioButtons() {
  const scenarios = state.rawData.scenarios;
  scenarioButtonsContainer.innerHTML = "";
  Object.keys(scenarios).forEach((key) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `scenario-btn ${key === state.currentScenario ? "active" : ""}`;
    btn.textContent = scenarios[key].title;
    btn.addEventListener("click", () => {
      state.currentScenario = key;
      renderScenarioButtons();
      updateDashboard();
    });
    scenarioButtonsContainer.appendChild(btn);
  });
}

function updateMetricCards() {
  const sc = state.rawData.scenarios[state.currentScenario];
  if (!sc) return;
  const { metrics } = sc;
  const currency = state.rawData.currency || "RUB";
  metricNodes.npv.textContent = formatMoney(metrics.NPV, currency);
  metricNodes.irr.textContent = formatPercent(metrics.IRR);
  metricNodes.pi.textContent = metrics.PI == null ? "—" : metrics.PI.toFixed(3);
  metricNodes.pp.textContent = formatYears(metrics.PP);
}

function createCashflowChart() {
  const ctx = document.getElementById("cashflowChart").getContext("2d");
  const scenario = state.rawData.scenarios[state.currentScenario];
  state.cashflowChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: state.rawData.years,
      datasets: [
        {
          label: `Денежный поток (${scenario.title})`,
          data: scenario.cashflow,
          borderWidth: 1,
          backgroundColor: scenario.cashflow.map((v) =>
            v >= 0 ? "rgba(52, 211, 153, 0.55)" : "rgba(248, 113, 113, 0.6)"
          ),
          borderColor: scenario.cashflow.map((v) =>
            v >= 0 ? "rgba(52, 211, 153, 1)" : "rgba(248, 113, 113, 1)"
          )
        }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
}

function updateCashflowChart() {
  const scenario = state.rawData.scenarios[state.currentScenario];
  state.cashflowChart.data.labels = state.rawData.years;
  const dataset = state.cashflowChart.data.datasets[0];
  dataset.label = `Денежный поток (${scenario.title})`;
  dataset.data = scenario.cashflow;
  dataset.backgroundColor = scenario.cashflow.map((v) =>
    v >= 0 ? "rgba(52, 211, 153, 0.55)" : "rgba(248, 113, 113, 0.6)"
  );
  dataset.borderColor = scenario.cashflow.map((v) =>
    v >= 0 ? "rgba(52, 211, 153, 1)" : "rgba(248, 113, 113, 1)"
  );
  state.cashflowChart.update();
}

function createComparisonChart() {
  const ctx = document.getElementById("comparisonChart").getContext("2d");
  const scenarios = state.rawData.scenarios;
  const { keys, labels, norm } = radarNormalizedData(scenarios);
  const colors = ["rgba(96, 165, 250, 0.7)", "rgba(52, 211, 153, 0.7)", "rgba(248, 113, 113, 0.7)"];
  state.comparisonChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels,
      datasets: keys.map((key, idx) => ({
        label: scenarios[key].title,
        data: norm[idx],
        borderColor: colors[idx % colors.length],
        backgroundColor: colors[idx % colors.length].replace("0.7", "0.2")
      }))
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
}

function updateComparisonChart() {
  const scenarios = state.rawData.scenarios;
  const { keys, labels, norm } = radarNormalizedData(scenarios);
  const colors = ["rgba(96, 165, 250, 0.7)", "rgba(52, 211, 153, 0.7)", "rgba(248, 113, 113, 0.7)"];
  state.comparisonChart.data.labels = labels;
  state.comparisonChart.data.datasets = keys.map((key, idx) => ({
    label: scenarios[key].title,
    data: norm[idx],
    borderColor: colors[idx % colors.length],
    backgroundColor: colors[idx % colors.length].replace("0.7", "0.2")
  }));
  state.comparisonChart.update();
}

function updateDashboard() {
  updateMetricCards();
  updateCashflowChart();
}

function renderAll() {
  renderScenarioButtons();
  updateMetricCards();
  if (!state.cashflowChart) createCashflowChart();
  else updateCashflowChart();
  if (!state.comparisonChart) createComparisonChart();
  else updateComparisonChart();
}

function showApiError(msg) {
  apiError.textContent = msg;
  apiError.hidden = false;
}

function hideApiError() {
  apiError.hidden = true;
  apiError.textContent = "";
}

async function handleRecalculate() {
  if (!parseAndValidateForm()) return;
  hideApiError();
  const payload = buildPayloadFromForm();
  try {
    const res = await fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(payload)
    });
    const body = await res.json();
    if (!body.ok) {
      showApiError(body.error || `Ошибка сервера (${res.status})`);
      return;
    }
    state.rawData = normalizeApiResult(body.result);
    state.currentScenario = "base";
    renderAll();
  } catch (e) {
    showApiError(
      "Не удалось связаться с сервером. Запустите из папки проекта: python api_server.py и откройте http://127.0.0.1:8000/"
    );
    console.error(e);
  }
}

analysisForm.addEventListener("submit", (event) => {
  event.preventDefault();
  handleRecalculate();
});

fileInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const text = await file.text();
    const payload = JSON.parse(text);
    const data = payload.inputParameters ? payload.inputParameters : payload;
    fillFormFromPayload(data);
    uploadStatus.textContent = `Файл ${file.name} загружен`;
    await handleRecalculate();
  } catch (error) {
    uploadStatus.textContent = `Ошибка: ${error.message}`;
  } finally {
    event.target.value = "";
  }
});

themeToggle.addEventListener("click", () => {
  document.body.classList.toggle("light");
});

analysisForm.querySelectorAll("input, select").forEach((node) => {
  node.addEventListener("input", () => {
    if (node.id) clearFieldError(node);
  });
  node.addEventListener("change", () => {
    if (node.id) clearFieldError(node);
  });
});

async function init() {
  try {
    const res = await fetch("./polya.json");
    if (res.ok) {
      const data = await res.json();
      fillFormFromPayload(data);
    }
  } catch (_) {
    /* поля по умолчанию из HTML */
  }
  await handleRecalculate();
}

init().catch((error) => {
  console.error("Ошибка инициализации:", error);
});
