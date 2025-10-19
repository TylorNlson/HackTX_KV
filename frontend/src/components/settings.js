import { useState } from "react";
import "./settings.css";

function Settings({setSummaryData, setPlotData, setPlotGalaxyData}) {
  // Sensible defaults so user can click Apply immediately
  const [settings, setSettings] = useState({
    track_id: "monaco",
    driver_mass: 75,
    car_mass: 798,
    max_power: 900,
    downforce: 5,
    drag: 1.2,
    reliability: 90,
    mileage: 1000,
    runs: 5000
  });

  const handleChange = (e) => {
    const { id, value, type } = e.target;
    const nextValue = type === "number" ? (value === "" ? "" : Number(value)) : value;
    setSettings((prev) => ({ ...prev, [id]: nextValue }));
  }

  const submitSettings = async () => {
    const hasEmptyField = Object.values(settings).some(value => value === "");
    if (hasEmptyField) {
      alert("Please fill in all fields before submitting.");
      const data = null;
      setSummaryData(data);
      const plotData = null;
      setPlotData(plotData);
      return;
    }

    console.log("Final settings to submit:", settings);

    try {
      const response = await fetch("http://127.0.0.1:8000/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
  
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      console.log("Simulation request successful:", response.status);
  
      const data = await response.json();

      console.log("Received simulation data:", data);
  
      setSummaryData({
        winRate: data[0].win_probability,
        meanTime: data[0].mean_time,
      });
  
      // --- Plot data for histogram & line chart ---
  
      setPlotData({
        hist_data: [100, 105, 110, 102, 108, 99, 107, 103],
        line_data: {
          x: [1, 2, 3, 4, 5, 6, 7, 8],
          y: [25, 26, 24, 27, 28, 26, 25, 29],
        },
      });
  
      // --- Galaxy data (scatter plot): use real values ---
      setPlotGalaxyData({
        x: [100, 105, 110, 102, 108, 99, 107, 103],
        y: [25, 26, 24, 27, 28, 26, 25, 29],
        size: [10, 15, 20, 12, 18, 14, 22, 17],
        label: [
          "1stop_L26_MH",
          "1stop_L39_MH",
          "1stop_L26_SH",
          "1stop_L39_SH",
          "1stop_L26_SM",
          "1stop_L39_SM",
          "1stop_L26_HM",
          "1stop_L39_HM",
        ],
      });
  
      console.log("Data processed successfully");
  
    } catch (error) {
      console.error("Simulation request failed:", error);
      alert("Failed to fetch simulation results. Check backend connection.");
    }
  }

  return (
    <div className="settings">
      <div className="settings-panel">
        <div className="settings-title">Settings</div>
        <hr/>
        <div className="env-settings">
          <div className="settings-subtitle">Environment Settings</div>
          <label htmlFor="track_id">Track Selection:</label>
          <select id="track_id" value={settings.track_id} onChange={handleChange}>
            <option value="monaco">Monaco</option>
            <option value="monza">Monza</option>
            <option value="spa">Spa</option>
            <option value="silverstone">Silverstone</option>
          </select>
          <br />
          <label htmlFor="driver_mass">Driver Mass:</label>
          <input id="driver_mass" type="number" value={settings.driver_mass} onChange={handleChange} />
        </div>
        <div className="car-setup">
          <div className="settings-subtitle">Car Setup</div>
          <label htmlFor="car_mass">Car Mass:</label>
          <input id="car_mass" type="number" value={settings.car_mass} onChange={handleChange} />
          <br />
          <label htmlFor="max_power">Max Power:</label>
          <input id="max_power" type="number" value={settings.max_power} onChange={handleChange} />
          <br />
          <label htmlFor="downforce">Downforce Level:</label>
          <input type="number" id="downforce" name="downforce" value={settings.downforce} onChange={handleChange}/>
          <br />
          <label htmlFor="drag">Drag:</label>
          <input type="number" id="drag" value={settings.drag} onChange={handleChange}/>
          <br />
          <label htmlFor="reliability">Reliability:</label>
          <input type="number" id="reliability" value={settings.reliability} onChange={handleChange}/>
          <br />
          <label htmlFor="mileage">Mileage:</label>
          <input type="number" id="mileage" value={settings.mileage} onChange={handleChange}/>
          <br />
          <button onClick={submitSettings}> Apply Settings </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;