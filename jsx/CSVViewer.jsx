import React, { useState } from "react";
import Papa from "papaparse";

// Файлы на сервере — заполни актуальные!
const files = [
  { date: "2024-07-30", filename: "outputs_2024-07-30.csv" },
  { date: "2024-07-29", filename: "outputs_2024-07-29.csv" },
  // Добавляй остальные...
];

const cellStyle = "px-2 py-1 border-b text-sm";
const thStyle = "bg-gray-200 px-2 py-1 border-b cursor-pointer select-none text-left";

function sortRows(rows, key, asc) {
  return [...rows].sort((a, b) => {
    if (!a[key]) return 1;
    if (!b[key]) return -1;
    if (key === "Цена") {
      let av = parseFloat((a[key] || "").replace(/[^0-9.,]/g, "").replace(",", "."));
      let bv = parseFloat((b[key] || "").replace(/[^0-9.,]/g, "").replace(",", "."));
      return asc ? av - bv : bv - av;
    }
    return asc
      ? (a[key] || "").localeCompare(b[key] || "")
      : (b[key] || "").localeCompare(a[key] || "");
  });
}

export default function CSVViewer() {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState("");
  const [sortKey, setSortKey] = useState("Запрос");
  const [sortAsc, setSortAsc] = useState(true);
  const [selectedDate, setSelectedDate] = useState(""); // для селектора даты

  async function loadFileByDate(date) {
    setSelectedDate(date);
    setRows([]); // Очистим данные на время загрузки
    if (!date) return;
    const file = files.find(f => f.date === date);
    if (!file) return;
    const res = await fetch(`/outputs/${file.filename}`); // папка с файлами
    const text = await res.text();
    Papa.parse(text, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        setRows(results.data);
      },
    });
  }

  function onFileChange(e) {
    setSelectedDate(""); // сбрасываем выбор даты
    const file = e.target.files[0];
    if (!file) return;
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        setRows(results.data);
      },
    });
  }

  function onDrop(e) {
    e.preventDefault();
    setSelectedDate(""); // сбрасываем выбор даты
    if (e.dataTransfer.files.length) {
      Papa.parse(e.dataTransfer.files[0], {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          setRows(results.data);
        },
      });
    }
  }

  function renderCell(cell, key) {
    if (
      typeof cell === "string" &&
      (cell.startsWith("http://") || cell.startsWith("https://"))
    ) {
      return (
        <a
          href={cell}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 underline break-all"
        >
          {cell}
        </a>
      );
    }
    return cell;
  }

  function copyAll() {
    let txt =
      (rows.length && Object.keys(rows[0]).join(";") + "\n") +
      rows.map((row) => Object.values(row).join(";")).join("\n");
    navigator.clipboard.writeText(txt);
    alert("Все строки скопированы в буфер обмена!");
  }

  // Фильтрация
  let filtered =
    filter.length > 0
      ? rows.filter((row) =>
          Object.values(row)
            .join(" ")
            .toLowerCase()
            .includes(filter.toLowerCase())
        )
      : rows;

  let sortedRows = sortRows(filtered, sortKey, sortAsc);

  return (
    <div className="max-w-6xl mx-auto p-4">
      <h2 className="text-2xl mb-2 font-bold">Таблица цен (outputs.csv)</h2>
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed rounded p-3 text-gray-500 hover:border-blue-500"
        >
          Перетащи свой CSV-файл или выбери вручную:
          <input
            type="file"
            accept=".csv"
            className="block mt-2"
            onChange={onFileChange}
          />
        </div>
        <div>
          <label className="font-semibold">Или выбери по дате: </label>
          <select
            value={selectedDate}
            className="border px-2 py-1 rounded"
            onChange={e => loadFileByDate(e.target.value)}
          >
            <option value="">-- Дата --</option>
            {files.map(f => (
              <option key={f.date} value={f.date}>{f.date}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex gap-2 mb-3">
        <input
          placeholder="Быстрый фильтр (любой текст)"
          className="border rounded px-2 py-1 w-72"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <button
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
          onClick={copyAll}
        >
          Копировать всё
        </button>
        <span className="text-sm text-gray-500">
          {sortedRows.length} результатов
        </span>
      </div>
      {sortedRows.length === 0 ? (
        <div className="text-gray-400 p-6">Нет данных</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border rounded bg-white">
            <thead>
              <tr>
                {Object.keys(sortedRows[0]).map((k) => (
                  <th
                    key={k}
                    className={thStyle}
                    onClick={() => {
                      if (sortKey === k) setSortAsc(!sortAsc);
                      else {
                        setSortKey(k);
                        setSortAsc(true);
                      }
                    }}
                  >
                    {k}
                    {sortKey === k ? (sortAsc ? " ▲" : " ▼") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, i) => (
                <tr key={i} className={i % 2 ? "bg-gray-50" : ""}>
                  {Object.keys(row).map((k) => (
                    <td key={k} className={cellStyle}>
                      {renderCell(row[k], k)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="text-xs text-gray-400 mt-6">
        <span>
          <b>Примечание:</b> Данные не отправляются на сервер, всё происходит в браузере. CSV должен иметь заголовки: <b>Запрос</b>, <b>Цена</b>, <b>Дата</b>, <b>Источник</b>, <b>Ссылка</b> (или аналогичные, см. свою выгрузку).
        </span>
      </div>
    </div>
  );
}
