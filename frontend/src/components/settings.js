import { useState } from "react";
import "./settings.css";

function Settings() {
  const [settings, setSettings] = useState({
    track: "",
    trackTemp: "",
    weather: "",
    grip: "",
    downforce: "",
    engineMode: "",
    fuelLoad: "",
    tireCompound: "",
    raceLength: "",
    tireCondition: "",
    safetyCarChance: "",
    competitorSpread: "",
    pitStopMin: "",
    pitStopMax: "",
    riskTolerance: "",
    targetFinish: ""
  });

  const handleChange = (e) => {
    e.preventDefault();
    setSettings({
      ...settings,
      [e.target.id]: e.target.value
    });
    console.log("Settings submitted:", {
      [e.target.id]: e.target.value
    });
  }

  const submitSettings = async () => {
    console.log("Final settings to submit:", settings);
  }

  return (
    <div className="settings">
      <div className="settings-panel">
        <div className="settings-title">Settings</div>
        <hr/>
        <div className="env-settings">
          <div className="settings-subtitle">Environment Settings</div>
          <label htmlFor="track">Track Selection:</label>
          <select id="track" onChange={handleChange}>
            <option value="monaco">Monaco</option>
            <option value="monza">Monza</option>
            <option value="spa">Spa</option>
            <option value="silverstone">Silverstone</option>
          </select>
          <br />
          <label htmlFor="trackTemp">Track Temperature (°C):</label>
          <input id="trackTemp" type="number" min="0" max="60" onChange={handleChange} />
          <br />
          <label htmlFor="weather">Weather:</label>
          <select id="weather" onChange={handleChange}>
            <option value="sunny">Sunny</option>
            <option value="cloudy">Cloudy</option>
            <option value="rain">Rain</option>
          </select>
          <br />
          <label htmlFor="grip">Track Grip Level:</label>
          <select id="grip" onChange={handleChange}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div className="car-setup">
          <div className="settings-subtitle">Car Setup</div>
          <label htmlFor="downforce">Downforce Level</label>
          <input type="range" id="downforce" name="downforce" min="1" max="10" onChange={handleChange}/>
          <br />
          <label htmlFor="engineMode">Engine Power Mode</label>
          <select id="engineMode" name="engineMode" onChange={handleChange}>
            <option value="eco">Eco</option>
            <option value="normal">Normal</option>
            <option value="aggressive">Aggressive</option>
          </select>
          <br />
          <label htmlFor="fuelLoad">Fuel Load (liters)</label>
          <input type="number" id="fuelLoad" name="fuelLoad" min="10" max="110" onChange={handleChange}/>
          <br />
          <label htmlFor="tireCompound">Tire Compound</label>
          <select id="tireCompound" name="tireCompound" onChange={handleChange}>
            <option value="soft">Soft</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
        <div className="race-conditions">
          <div className="settings-subtitle">Race Conditions</div>
          <label htmlFor="raceLength">Race Length (laps)</label>
          <input type="number" id="raceLength" name="raceLength" min="1" max="100" onChange={handleChange}/>
          <br />
          <label htmlFor="tireCondition">Initial Tire Condition</label>
          <select id="tireCondition" name="tireCondition" onChange={handleChange}>
            <option value="fresh">Fresh</option>
            <option value="worn">Partially Worn</option>
          </select>
          <br />
          <label htmlFor="safetyCarChance">Expected Safety Car Chance (%)</label>
          <input type="number" id="safetyCarChance" name="safetyCarChance" min="0" max="100" onChange={handleChange}/>
          <label htmlFor="competitorSpread">Competitor Performance Spread</label>
          <input type="range" id="competitorSpread" name="competitorSpread" min="0" max="10" onChange={handleChange}/>
        </div>
        <div className="strategy">
          <div className="settings-subtitle">Strategy</div>
          <label htmlFor="pitStopMin">Pit Stop Window (Min Lap)</label>
          <input type="number" id="pitStopMin" name="pitStopMin" min="1" onChange={handleChange}/>
          <br />
          <label htmlFor="pitStopMax">Pit Stop Window (Max Lap)</label>
          <input type="number" id="pitStopMax" name="pitStopMax" min="1" onChange={handleChange}/>
          <br />
          <label htmlFor="riskTolerance">Risk Tolerance</label>
          <select id="riskTolerance" name="riskTolerance" onChange={handleChange}>
            <option value="conservative">Conservative</option>
            <option value="balanced">Balanced</option>
            <option value="aggressive">Aggressive</option>
          </select>
          <br />
          <label htmlFor="targetFinish">Target Finish Position</label>
          <select id="targetFinish" name="targetFinish" onChange={handleChange}>
            <option value="p1">P1</option>
            <option value="top3">Top 3</option>
            <option value="top5">Top 5</option>
            <option value="points">Points (Top 10)</option>
          </select>
          <button onClick={submitSettings}> Apply Settings </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;