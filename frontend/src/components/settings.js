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
  
      // Depending on your backend, adjust these keys:
      // Example expected: { winRate, raceTime, dnfRate, hist_data, line_data, galaxy_data }
      setSummaryData({
        winRate: data.winRate,
        raceTime: data.raceTime,
        dnfRate: data.dnfRate,
      });
  
      if (data.hist_data && data.line_data) {
        setPlotData({
          hist_data: data.hist_data,
          line_data: data.line_data,
        });
      }
  
      if (data.galaxy_data) {
        setPlotGalaxyData(data.galaxy_data);
      }
  
    } catch (error) {
      console.error("Simulation request failed:", error);
      console.log("Using mock data since backend is not available");
      
      // Generate mock data for demonstration
      const mockHistData = Array.from({length: 50}, (_, i) => 85 + Math.random() * 10);
      const mockLineData = Array.from({length: 20}, (_, i) => ({
        lap: i + 1,
        time: 88 + Math.random() * 3
      }));
      const mockGalaxyData = Array.from({length: 100}, () => ({
        x: Math.random() * 10 - 5,
        y: Math.random() * 10 - 5,
        z: Math.random() * 10 - 5,
        color: Math.random(),
        size: Math.random() * 5 + 2
      }));
      
      setSummaryData({
        winRate: (Math.random() * 30 + 10).toFixed(1) + "%",
        raceTime: (85 + Math.random() * 5).toFixed(2) + "s",
        dnfRate: (Math.random() * 5).toFixed(1) + "%",
      });
      
      setPlotData({
        hist_data: mockHistData,
        line_data: mockLineData,
      });
      
      setPlotGalaxyData(mockGalaxyData);
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