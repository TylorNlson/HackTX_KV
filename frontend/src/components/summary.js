import "./summary.css";

function Summary({data}) {
  return (
    <div className="summary">
      <div className="summary-panel">
        {data ? 
            <div>
                <p>This strategy wins {data.winRate} of the time.</p> 
                <p>Average total race time = {data.raceTime} seconds.</p> 
                <p>Fuel constraint causes DNF in {data.dnfRate} of cases.</p>
            </div>
            : <p>No summary available.</p>}
      </div>
    </div>
  );
}

export default Summary;