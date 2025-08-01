import React, { useState } from "react";
import Papa from "papaparse";

// Тут твой список CSV-файлов
const files = [
  { date: "2024-07-30", filename: "outputs_2024-07-30.csv" },
  { date: "2024-07-29", filename: "outputs_2024-07-29.csv" },
  // Добавь остальные файлы
];

export default function CsvViewer() {
  const [selected, setSelected] = useState("");
  const [data, setData] = useState([]);

  // Срабатывает при выборе даты
  const handleChange = async (e) => {
    const date = e.target.value;
    setSelected(date);
    const file = files.find(f => f.date === date);
    if (!file) return setData([]);
    const res = await fetch(`/outputs/${file.filename}`); // путь к папке с CSV
    const text = await res.text();
    Papa.parse(text, {
      header: true,
      skipEmptyLines: true,
      complete: results => setData(results.data),
    });
  };

  return (
    <div>
      <label>Выберите дату:{" "}
        <select value={selected} onChange={handleChange}>
          <option value="">-- Дата --</option>
          {files.map(f => (
            <option key={f.date} value={f.date}>{f.date}</option>
          ))}
        </select>
      </label>
      <div style={{ marginTop: 16 }}>
        {data.length > 0 &&
          <table border={1} cellPadding={6}>
            <thead>
              <tr>
                {Object.keys(data[0]).map(col => <th key={col}>{col}</th>)}
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <tr key={idx}>
                  {Object.values(row).map((val, i) => <td key={i}>{val}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        }
      </div>
    </div>
  );
}
