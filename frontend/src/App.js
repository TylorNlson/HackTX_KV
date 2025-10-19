import "./App.css";
import { useState } from "react";
import SummaryPanel from "./components/summary";
import SettingsPanel from "./components/settings";
import GalaxyPanel from "./components/galaxy";
import GraphsPanel from "./components/graphs";

function App() {
  const [summaryData, setSummaryData] = useState(null);
  const [plotData, setPlotData] = useState(null);
  const [plotGalaxyData, setPlotGalaxyData] = useState(null);
  
  return (
    <div className="App">
      <div className="App-background" alt="space background">
        <div className="App-dashboard">
          <SettingsPanel setSummaryData={setSummaryData} setPlotData={setPlotData} setPlotGalaxyData={setPlotGalaxyData}/>
          <SummaryPanel data={summaryData}/>
          {/* Pass the prop name Galaxy expects */}
          <GalaxyPanel plotData={plotGalaxyData}/>
          <GraphsPanel plotData={plotData}/>
        </div>
      </div>
    </div>
  );
}

export default App;
