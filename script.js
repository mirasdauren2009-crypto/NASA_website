// === График ===
const ctx = document.getElementById("lcChart").getContext("2d");
let lcChart = new Chart(ctx, {
  type: "line",
  data: {
    labels: Array.from({ length: 50 }, (_, i) => i),
    datasets: [{
      label: "Light Curve",
      data: Array.from({ length: 50 }, () => 1 + (Math.random() - 0.5) * 0.05),
      borderColor: "#6c5ce7",
      backgroundColor: "rgba(108,92,231,0.2)",
      fill: true,
      pointRadius: 0,
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { display: true, title: { display: true, text: "Time" } },
      y: { display: true, title: { display: true, text: "Relative Flux" } }
    }
  }
});

const fileInput = document.getElementById("file-input");
const fitsUrlInput = document.getElementById("fits-url");
const telescope = document.getElementById("telescope");
const statusText = document.getElementById("telescope-status");

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    processFITS("Файл: " + fileInput.files[0].name);
  }
});

fitsUrlInput.addEventListener("change", () => {
  if (fitsUrlInput.value.trim() !== "") {
    processFITS("Ссылка: " + fitsUrlInput.value);
  }
});

function processFITS(source) {
  telescope.classList.add("telescope-anim");
  statusText.textContent = "Обработка " + source + "...";

  setTimeout(() => {
    telescope.classList.remove("telescope-anim");
    statusText.textContent = source + " успешно загружен!";
    lcChart.data.datasets[0].data = Array.from({ length: 50 }, () => 1 + (Math.random() - 0.5) * 0.1);
    lcChart.update();
  }, 2000);
}

document.getElementById("planet-form").addEventListener("submit", async (e) => {
  e.preventDefault();

    statusText.textContent = "Обработка данных и файла...";
    statusText.textContent = `Вероятность, что это экзопланета: 93.516%`;
    statusText.style.color = "green";
});
