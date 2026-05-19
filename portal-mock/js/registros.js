(function () {
  function formatDateBr(isoDate) {
    const parts = isoDate.split("-");
    return parts[2] + "/" + parts[1] + "/" + parts[0];
  }

  function renderTable(records) {
    const tbody = document.querySelector('[data-testid="registros-table"] tbody');
    tbody.innerHTML = "";

    records.forEach(function (row) {
      const tr = document.createElement("tr");
      tr.setAttribute("data-testid", "registro-row");
      tr.innerHTML =
        '<td data-testid="col-matricula">' +
        row.employee_id +
        "</td>" +
        '<td data-testid="col-nome">' +
        row.employee_name +
        "</td>" +
        '<td data-testid="col-data">' +
        formatDateBr(row.work_date) +
        "</td>" +
        '<td data-testid="col-entrada">' +
        row.check_in +
        "</td>" +
        '<td data-testid="col-saida">' +
        row.check_out +
        "</td>";
      tbody.appendChild(tr);
    });

    document.getElementById("record-count").textContent = String(records.length);
  }

  fetch("data/batidas.json")
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Falha ao carregar batidas.json");
      }
      return response.json();
    })
    .then(renderTable)
    .catch(function (err) {
      console.error(err);
      document.getElementById("load-error").style.display = "block";
    });
})();
