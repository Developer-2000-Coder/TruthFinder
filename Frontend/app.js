
const searchInput = document.getElementById("searchInput");
const resultsContainer = document.getElementById("results");
const bm25Slider = document.getElementById("bm25Weight");
const bm25Val = document.getElementById("bm25Val");
const sortSelect = document.getElementById("sortSelect");
const loadingSpinner = document.getElementById("loading");
const searchBtn = document.getElementById("searchBtn");

let searchTimeout = null;

bm25Slider.addEventListener("input", () => {
    bm25Val.textContent = parseFloat(bm25Slider.value).toFixed(2);
    triggerSearch();
});

sortSelect.addEventListener("change", () => {
    triggerSearch();
});

searchBtn.addEventListener("click", () => {
    triggerSearch();
});

searchInput.addEventListener("input", () => {
    triggerSearch();
});

function triggerSearch() {
    clearTimeout(searchTimeout);
    const query = searchInput.value.trim();
    if (!query) {
        resultsContainer.innerHTML = "<p>Type something to search...</p>";
        return;
    }
    searchTimeout = setTimeout(() => {
        search(query);
    }, 300);
}

async function search(query) {
    const bm25Weight = parseFloat(bm25Slider.value);
    const sortOption = sortSelect.value;

    loadingSpinner.style.display = "block";
    resultsContainer.innerHTML = "";

    try {
        const response = await fetch(`http://127.0.0.1:8000/search?q=${encodeURIComponent(query)}&bm25_weight=${bm25Weight}&sort=${sortOption}`);
        if (!response.ok) throw new Error("Network error");
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error("Search error:", error);
        resultsContainer.innerHTML = "<p style='color:red;'>Error connecting to backend.</p>";
    } finally {
        loadingSpinner.style.display = "none";
    }
}

function displayResults(data) {
    resultsContainer.innerHTML = "";

    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = "<p>No results found.</p>";
        return;
    }

    data.results.forEach(result => {
        const div = document.createElement("div");
        div.classList.add("result-card", "mb-3");

        let credClass = "cred-medium";
        if (result.credibility_score >= 0.8) credClass = "cred-high";
        else if (result.credibility_score <= 0.5) credClass = "cred-low";

        div.innerHTML = `
            <h5 class="fw-bold"><a href="${result.url}" target="_blank">${result.title}</a></h5>
            <div class="text-muted small mb-1">
                Source: ${result.source || "Unknown"} | Published: ${result.published_date || "N/A"}
            </div>
            <p>${result.content || result.summary || ""}</p>
            <div class="d-flex justify-content-between align-items-center">
                <div class="cred-pill ${credClass}">
                    Credibility: ${result.credibility_score.toFixed(2)}
                </div>
                <a href="${result.url}" target="_blank" class="btn btn-sm btn-outline-primary">Read</a>
            </div>
        `;
        resultsContainer.appendChild(div);
    });
}

searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") triggerSearch();
});

resultsContainer.innerHTML = "<p>Type something to search...</p>";
