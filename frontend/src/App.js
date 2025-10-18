import "./App.css";
import SummaryPanel from "./components/summary";
import SettingsPanel from "./components/settings";
import GalaxyPanel from "./components/galaxy";

function App() {
  return (
    <div className="App">
      <div className="App-background" alt="space background">
        <div className="App-dashboard">
          <SettingsPanel />
          <SummaryPanel />
          <GalaxyPanel />
        </div>
      </div>
    </div>
  );
}

export default App;
