import Plot from 'react-plotly.js';
import "./galaxy.css"; // optional shared styling

function Galaxy({ plotData }) {
  if (!plotData) {
    return (
      <div className="galaxy">
        <div className="galaxy-panel">
          No plot data available.
        </div>
      </div>
    );
  }

  // generate random data
  const N = 5000;
  const x = Array.from({ length: N }, () => Math.random());
  const y = Array.from({ length: N }, () => Math.random());
  const successRate = plotData.successRate;
  const labels = Array.from({ length: N }, (_, i) => `Point ${i + 1}`);

  return (
    <div className="galaxy">
      <div className="galaxy-panel">
        <div className="galaxy-container">
          <Plot
            data={[
              {
                x: plotData.x,
                y: plotData.y,
                type: 'scatter',
                marker: 'markers',
                color: 'white',
                opacity: 1,
                name: 'Laps',
              },
            ]}
            layout={{
              title: 'Lap Data',
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

        <div className="galaxy-container">
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

export default Galaxy;