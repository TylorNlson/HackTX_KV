import Plot from 'react-plotly.js';
import "./graphs.css";

function Graphs({ plotData }) {
  if (!plotData) {
    return (
      <div className="graphs">
        <div className="graphs-panel">
          No plot data available.
        </div>
      </div>
    );
  }

  return (
    <div className="graphs">
      <div className="graphs-panel">
        <div className="graph-container">
          <Plot
            data={[
              {
                x: plotData.hist_data,
                type: 'histogram',
                marker: { color: 'skyblue' },
                opacity: 0.8,
                name: 'Lap Time Distribution',
              },
            ]}
            layout={{
              title: 'Lap Time Distribution',
              xaxis: { title: 'Lap Time (s)', color: '#fff' },
              yaxis: { title: 'Frequency', color: '#fff' },
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { color: 'white' },
              margin: { t: 50, l: 50, r: 50, b: 50 },
              autosize: true
            }}
            style={{ width: '100%', height: '100%' }}
            config={{ responsive: true }}
          />
        </div>

        <div className="graph-container">
          <Plot
            data={[
              {
                x: plotData.line_data.x,
                y: plotData.line_data.y,
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: 'red', width: 2 },
                marker: { size: 6 },
                name: 'Average Lap Time Over Laps',
              },
            ]}
            layout={{
              title: 'Average Lap Time Over Laps',
              xaxis: { title: 'Lap', color: '#fff' },
              yaxis: { title: 'Average Lap Time (s)', color: '#fff' },
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { color: 'white' },
              margin: { t: 50, l: 50, r: 50, b: 50 },
              autosize: true
            }}
            style={{ width: '100%', height: '100%' }}
            config={{ responsive: true }}
          />
         </div>
      </div>
    </div>
  );
}

export default Graphs;