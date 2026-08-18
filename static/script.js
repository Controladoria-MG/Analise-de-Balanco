let dados = [];

async function carregar() {
  try {
    const [respDados, respStatus] = await Promise.all([
      fetch("data/analise_balanco/analise_balanco_dados.json"),
      fetch("data/analise_balanco/status.json"),
    ]);
    dados = await respDados.json();
    const status = await respStatus.json();
    document.getElementById("status-atualizacao").textContent =
      `Última atualização: ${new Date(status.ultima_execucao).toLocaleString("pt-BR")} — ${status.registros} empresas`;
  } catch (e) {
    document.getElementById("status-atualizacao").textContent =
      "Sem dados ainda — rode os robôs em backend/ para gerar o resumo.";
    dados = [];
  }
  aplicarFiltros();
}

function aplicarFiltros() {
  const busca = document.getElementById("f-busca").value.trim().toLowerCase();
  const doc = document.getElementById("f-documentacao").value;

  const filtrados = dados.filter((el) => {
    if (busca && !String(el.Cliente || "").toLowerCase().includes(busca)) return false;
    if (doc && el["Documentação"] !== doc) return false;
    return true;
  });

  renderizarKpis(filtrados);
  renderizarTabela(filtrados);
}

function renderizarKpis(lista) {
  const pendente = lista.filter((el) => el["Documentação"] === "Documentação Pendente").length;
  const recebida = lista.filter((el) => el["Documentação"] === "Documentação Recebida").length;
  document.getElementById("kpi-total").textContent = lista.length;
  document.getElementById("kpi-pendente").textContent = pendente;
  document.getElementById("kpi-recebida").textContent = recebida;
}

function renderizarTabela(lista) {
  const corpo = document.getElementById("tabela-corpo");
  corpo.innerHTML = "";

  if (lista.length === 0) {
    corpo.innerHTML = `<tr><td colspan="2" class="vazio">Nenhum registro encontrado.</td></tr>`;
    return;
  }

  for (const el of lista) {
    const tr = document.createElement("tr");
    const classeDoc = el["Documentação"] === "Documentação Pendente" ? "doc-pendente" : "doc-recebida";
    tr.innerHTML = `
      <td>${el.Cliente ?? ""}</td>
      <td class="${classeDoc}">${el["Documentação"] ?? ""}</td>
    `;
    corpo.appendChild(tr);
  }
}

function alternarTema() {
  document.body.classList.toggle("tema-escuro");
  const escuro = document.body.classList.contains("tema-escuro");
  document.getElementById("btn-tema").textContent = escuro ? "☀️" : "🌙";
  localStorage.setItem("analise-balanco-tema", escuro ? "escuro" : "claro");
}

document.getElementById("f-busca").addEventListener("input", aplicarFiltros);
document.getElementById("f-documentacao").addEventListener("change", aplicarFiltros);
document.getElementById("btn-tema").addEventListener("click", alternarTema);

if (localStorage.getItem("analise-balanco-tema") === "escuro") {
  document.body.classList.add("tema-escuro");
  document.getElementById("btn-tema").textContent = "☀️";
}

carregar();
