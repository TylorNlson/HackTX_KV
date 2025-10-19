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
    front_wing_angle: 5,
    rear_wing_angle: 5,
    air_roll_balance: 0,
    front_spring_rate: 150,
    rear_spring_rate: 150,
    tire_preasure_front: 22,
    tire_preasure_back: 21,
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

    // TO DO back end call for summary data
    // const data = await response.json();
    const data = {winRate: 75, raceTime: 5400, dnfRate: 5}; // TO DO place holder data
    setSummaryData(data);

    // TO DO back end call for plot data
    const plotData = {hist_data: [80, 82, 79, 81, 83, 78, 80, 82], line_data: {x: [1,2,3,4,5,6,7,8], y: [81,80.5,80.2,80.1,80.0,79.8,79.7,79.5]}}; // TO DO place holder data
    setPlotData(plotData);

    const plotGalaxyData = {x: [1,2,3,4,5], y: [10,20,15,25,30], size: [5,10,15,20,25]}; // TO DO place holder data
    setPlotGalaxyData(plotGalaxyData);
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
          <label htmlFor="front_wing_angle">Front Wing Angle:</label>
          <input type="number" id="front_wing_angle" value={settings.front_wing_angle} onChange={handleChange} />
          <br />
          <label htmlFor="rear_wing_angle">Rear Wing Angle:</label>
          <input type="number" id="rear_wing_angle" value={settings.rear_wing_angle} onChange={handleChange} />
          <br />
          <label htmlFor="air_roll_balance">Air Roll Balance:</label>
          <input type="number" id="air_roll_balance" value={settings.air_roll_balance} onChange={handleChange} />
          <br />
          <label htmlFor="front_spring_rate">Front Spring Rate:</label>
          <input type="number" id="front_spring_rate" value={settings.front_spring_rate} onChange={handleChange} />
          <br />
          <label htmlFor="rear_spring_rate">Rear Spring Rate:</label>
          <input type="number" id="rear_spring_rate" value={settings.rear_spring_rate} onChange={handleChange} />
          <br />
          <label htmlFor="tire_preasure_front">Tire Pressure (Front):</label>
          <input type="number" id="tire_preasure_front" value={settings.tire_preasure_front} onChange={handleChange} />
          <br />
          <label htmlFor="tire_preasure_back">Tire Pressure (Back):</label>
          <input type="number" id="tire_preasure_back" value={settings.tire_preasure_back} onChange={handleChange} />
          <br />
        </div>
        <div className="race-conditions">
          <div className="settings-subtitle">Race Conditions</div>
          <label htmlFor="runs">Runs:</label>
          <input type="number" id="runs" value={settings.runs} onChange={handleChange} />
          <br />
          <button onClick={submitSettings}> Apply Settings </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;