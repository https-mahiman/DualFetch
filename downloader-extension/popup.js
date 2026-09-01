document.addEventListener("DOMContentLoaded", async () => {
  const urlInput = document.getElementById("pageUrl");
  const downloadBtn = document.getElementById("downloadBtn");
  const btnText = downloadBtn.querySelector(".btn-text");
  const spinner = downloadBtn.querySelector(".spinner");
  const statusMessage = document.getElementById("statusMessage");
  const resultBox = document.getElementById("resultBox");
  const mediaTitle = document.getElementById("mediaTitle");
  const saveFolder = document.getElementById("saveFolder");

  // 1. Automatically retrieve the active tab's URL
  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (tab && tab.url && !tab.url.startsWith("chrome://")) {
      urlInput.value = tab.url;
    } else {
      urlInput.placeholder = "Paste a video or audio URL manually";
    }
  } catch (err) {
    urlInput.placeholder = "Paste media URL manually";
  }

  // 2. Handle the download click
  downloadBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    const selectedType = document.querySelector(
      'input[name="downloadType"]:checked',
    ).value;

    if (!url) {
      statusMessage.textContent = "Please enter or open a valid URL.";
      statusMessage.className = "status error";
      return;
    }

    // UI Loading State
    statusMessage.className = "status hidden";
    resultBox.classList.add("hidden");
    downloadBtn.disabled = true;
    btnText.textContent = `Downloading ${selectedType}...`;
    spinner.classList.remove("hidden");

    try {
      const response = await fetch(
        "https://dualfetch-api.onrender.com/download",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: url,
            type: selectedType,
          }),
        },
      );

      const data = await response.json();

      if (data.success) {
        statusMessage.textContent = "Download Complete!";
        statusMessage.className = "status success";

        mediaTitle.textContent = data.title || "Downloaded Item";
        saveFolder.textContent = `${data.folder}/`;
        resultBox.classList.remove("hidden");
      } else {
        statusMessage.textContent = data.error || "Download failed.";
        statusMessage.className = "status error";
      }
    } catch (err) {
      statusMessage.textContent =
        "Backend unreachable. Make sure Flask is running on port 5000.";
      statusMessage.className = "status error";
    } finally {
      downloadBtn.disabled = false;
      btnText.textContent = "Download Now";
      spinner.classList.add("hidden");
    }
  });
});
