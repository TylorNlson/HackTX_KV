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
  
      const raceResults = data.results;
      const totalRuns = raceResults.length;

      // Example: if multiple entries share the same strategy name, count frequency
      const strategyCounts = {};
      raceResults.forEach(r => {
        strategyCounts[r.name] = (strategyCounts[r.name] || 0) + 1;
      });
  
      // Find most common strategy
      const [topStrategy, topCount] = Object.entries(strategyCounts).reduce(
        (a, b) => (b[1] > a[1] ? b : a),
        ["None", 0]
      );
  
      // Compute averages
      const avgFuel =
        raceResults.reduce((sum, r) => sum + r.starting_fuel, 0) / totalRuns;
      const avgPitLap =
        raceResults.reduce((sum, r) => sum + (r.pit_laps?.[0] ?? 0), 0) /
        totalRuns;
  
      // Fill in summary data using meaningful values from your response
      setSummaryData({
        winRate: ((topCount / totalRuns) * 100).toFixed(1), // % of top strategy
        raceTime: (avgPitLap * 200).toFixed(0), // Example: pit lap proxy for race time
        dnfRate: ((totalRuns - topCount) / totalRuns * 100).toFixed(1), // others as DNF
        topStrategy: topStrategy,
        avgFuel: avgFuel.toFixed(1),
      });
  
      // --- Plot data for histogram & line chart ---
  
      setPlotData({
        hist_data: raceResults.map(r => r.starting_fuel),
        line_data: {
          x: raceResults.map((_, i) => i + 1),
          y: raceResults.map(r => r.pit_laps?.[0] ?? 0),
        },
      });
  
      // --- Galaxy data (scatter plot): use real values ---
      setPlotGalaxyData({
        x: raceResults.map(r => r.starting_fuel),
        y: raceResults.map(r => r.pit_laps?.[0] ?? 0),
        size: raceResults.map(r => {
          const compounds = r.tire_compounds?.length || 1;
          return compounds * 10; // use number of tire compounds as visual size factor
        }),
        label: raceResults.map(r => r.name),
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