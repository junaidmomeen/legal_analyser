// src/api/analyze.ts

// No authentication required; direct calls

export async function analyzeDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://localhost:8000/analyze", {
    method: "POST",
    headers: {},
    body: formData,
  });

  if (!response.ok) throw new Error("Failed to analyze document");
  return response.json();
}

export async function exportAnalysis(fileId: string, format: "pdf" | "json") {
  const response = await fetch(`http://localhost:8000/export/${fileId}/${format}`, {
    method: "GET",
    headers: {},
  });

  if (!response.ok) throw new Error(`Failed to export ${format}`);

  // For JSON, force file download
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `analysis.${format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();

  window.URL.revokeObjectURL(url);
}
