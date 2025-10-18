// F1 Race Decision System - Frontend JavaScript
const API_BASE_URL = 'http://localhost:5000/api';

// Update slider values
document.getElementById('dragCoef').addEventListener('input', (e) => {
    document.getElementById('dragValue').textContent = e.target.value;
});

document.getElementById('downforce').addEventListener('input', (e) => {
    document.getElementById('downforceValue').textContent = e.target.value;
});

// Get Real-Time Decision
async function getRealTimeDecision() {
    const decisionResult = document.getElementById('decisionResult');
    decisionResult.innerHTML = '<div class="loading"></div> <p>Analyzing race context...</p>';
    
    try {
        const raceContext = {
            current_lap: parseInt(document.getElementById('currentLap').value),
            total_laps: 60,
            current_position: parseInt(document.getElementById('position').value),
            tire_age: parseInt(document.getElementById('tireAge').value),
            tire_compound: document.getElementById('tireCompound').value,
            fuel_remaining: parseFloat(document.getElementById('fuelRemaining').value),
            gap_to_leader: parseFloat(document.getElementById('gapLeader').value),
            gap_to_next: parseFloat(document.getElementById('gapNext').value),
            track_temp: parseFloat(document.getElementById('trackTemp').value),
            weather_forecast: 'dry'
        };
        
        const response = await fetch(`${API_BASE_URL}/decision/realtime`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ race_context: raceContext })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayDecision(data.decision, data.prediction);
            displayStrategySummary(data.summary);
        } else {
            decisionResult.innerHTML = `<p class="error">Error: ${data.error}</p>`;
        }
    } catch (error) {
        decisionResult.innerHTML = `<p class="error">Error connecting to API: ${error.message}</p>`;
    }
}

// Display Decision
function displayDecision(decision, prediction) {
    const decisionResult = document.getElementById('decisionResult');
    
    const urgencyClass = `urgency-${decision.urgency}`;
    
    let html = `
        <div class="decision-highlight ${urgencyClass}">
            ${decision.recommended_action}
        </div>
        
        <div style="margin-top: 15px;">
            <h3 style="color: var(--accent-color); margin-bottom: 10px;">Race Context</h3>
            <p><strong>Lap:</strong> ${decision.context.lap} | 
               <strong>Position:</strong> P${decision.context.position} | 
               <strong>Tire:</strong> ${decision.context.tire_compound.toUpperCase()} (${decision.context.tire_age} laps)</p>
            <p><strong>Fuel:</strong> ${decision.context.fuel.toFixed(1)} kg remaining</p>
        </div>
        
        <div style="margin-top: 15px;">
            <h3 style="color: var(--accent-color); margin-bottom: 10px;">Rationale</h3>
            <ul class="rationale-list">
    `;
    
    decision.rationale.forEach(reason => {
        html += `<li>${reason}</li>`;
    });
    
    html += `
            </ul>
        </div>
        
        <div style="margin-top: 15px;">
            <h3 style="color: var(--accent-color); margin-bottom: 10px;">Race Prediction</h3>
            <p><strong>Predicted Finish:</strong> P${prediction.predicted_position}</p>
            <p><strong>Confidence:</strong> ${prediction.confidence}</p>
            <div style="margin-top: 10px; font-size: 0.9em;">
                <strong>Scenarios:</strong><br>
                Best: P${prediction.scenarios.best_case} | 
                Likely: P${prediction.scenarios.likely} | 
                Worst: P${prediction.scenarios.worst_case}
            </div>
        </div>
    `;
    
    decisionResult.innerHTML = html;
}

// Run Strategy Simulation
async function runStrategySimulation() {
    const strategyResults = document.getElementById('strategyResults');
    const strategySummary = document.getElementById('strategySummary');
    strategyResults.innerHTML = '<div class="loading"></div> <p>Running HPC simulations...</p>';
    
    try {
        const weather = document.getElementById('weatherCondition').value;
        
        const response = await fetch(`${API_BASE_URL}/simulate/strategies`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ weather: weather })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayStrategyResults(data.simulation_results, data.analysis);
            displayStrategySummaryFromSim(data.simulation_results);
            
            // Update performance metrics
            updatePerformanceMetrics(data.simulation_results);
        } else {
            strategyResults.innerHTML = `<p class="error">Error: ${data.error}</p>`;
        }
    } catch (error) {
        strategyResults.innerHTML = `<p class="error">Error connecting to API: ${error.message}</p>`;
    }
}

// Display Strategy Results
function displayStrategyResults(simulationResults, analysis) {
    const strategyResults = document.getElementById('strategyResults');
    
    let html = `
        <h3 style="color: var(--success); margin-bottom: 15px;">
            ✓ Evaluated ${simulationResults.strategies_evaluated} strategies in ${(simulationResults.processing_time * 1000).toFixed(0)}ms
        </h3>
    `;
    
    // Display top 3 strategies
    simulationResults.results.slice(0, 3).forEach((result, index) => {
        const tireStrategy = result.strategy.map(s => 
            `<span class="tire-badge tire-${s[0]}">${s[0].toUpperCase()} (${s[1]} laps)</span>`
        ).join(' → ');
        
        html += `
            <div class="strategy-item">
                <h3>Strategy ${index + 1} - Rank #${result.rank}</h3>
                <p><strong>Tire Strategy:</strong> ${tireStrategy}</p>
                <p><strong>Total Race Time:</strong> ${result.total_time.toFixed(1)}s</p>
                <p><strong>Average Lap Time:</strong> ${result.average_lap_time.toFixed(2)}s</p>
                <p><strong>Pit Stops:</strong> ${result.num_pit_stops}</p>
                ${result.time_delta > 0 ? `<p><strong>Time Delta:</strong> +${result.time_delta.toFixed(1)}s</p>` : ''}
            </div>
        `;
    });
    
    strategyResults.innerHTML = html;
}

// Display Strategy Summary
function displayStrategySummary(summary) {
    const strategySummary = document.getElementById('strategySummary');
    
    let html = `
        <div style="background: var(--bg-dark); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="color: var(--accent-color); margin-bottom: 10px;">Executive Summary</h3>
            <p>${summary.executive_summary}</p>
        </div>
        
        <h3 style="color: var(--accent-color); margin-bottom: 10px;">Key Insights</h3>
        <ul class="rationale-list">
    `;
    
    summary.key_insights.forEach(insight => {
        html += `<li>${insight}</li>`;
    });
    
    html += `
        </ul>
        
        <h3 style="color: var(--accent-color); margin: 15px 0 10px 0;">Risk Assessment</h3>
        <div style="background: var(--bg-dark); padding: 15px; border-radius: 8px;">
    `;
    
    for (const [key, value] of Object.entries(summary.risk_assessment)) {
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `<p><strong>${label}:</strong> ${value}</p>`;
    }
    
    html += `
        </div>
        
        <h3 style="color: var(--accent-color); margin: 15px 0 10px 0;">Communication Notes</h3>
        <ul class="rationale-list">
    `;
    
    summary.communication_notes.forEach(note => {
        html += `<li>${note}</li>`;
    });
    
    html += '</ul>';
    
    strategySummary.innerHTML = html;
}

// Display Strategy Summary from Simulation
function displayStrategySummaryFromSim(simulationResults) {
    // This would generate a summary similar to displayStrategySummary
    // but from simulation results directly
    const strategySummary = document.getElementById('strategySummary');
    
    const best = simulationResults.results[0];
    
    let html = `
        <div style="background: var(--bg-dark); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="color: var(--accent-color); margin-bottom: 10px;">Best Strategy</h3>
            <p>Recommended ${best.num_pit_stops}-stop strategy</p>
            <p>Expected race time: ${best.total_time.toFixed(1)}s</p>
        </div>
        
        <h3 style="color: var(--accent-color); margin-bottom: 10px;">Top 3 Strategies</h3>
    `;
    
    simulationResults.results.slice(0, 3).forEach((result, i) => {
        html += `
            <div style="padding: 10px; background: var(--bg-dark); border-radius: 6px; margin-bottom: 10px;">
                <strong>Option ${i + 1}:</strong> ${result.time_delta.toFixed(1)}s slower
            </div>
        `;
    });
    
    strategySummary.innerHTML = html;
}

// Simulate Aero Setup
async function simulateAeroSetup() {
    const aeroResults = document.getElementById('aeroResults');
    aeroResults.innerHTML = '<div class="loading"></div> <p>Simulating aerodynamic setup...</p>';
    
    try {
        const dragCoef = parseFloat(document.getElementById('dragCoef').value);
        const downforce = parseFloat(document.getElementById('downforce').value);
        
        const response = await fetch(`${API_BASE_URL}/simulate/aero-setup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                drag_coefficient: dragCoef,
                downforce_level: downforce
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayAeroResults(data.result);
        } else {
            aeroResults.innerHTML = `<p class="error">Error: ${data.error}</p>`;
        }
    } catch (error) {
        aeroResults.innerHTML = `<p class="error">Error connecting to API: ${error.message}</p>`;
    }
}

// Display Aero Results
function displayAeroResults(result) {
    const aeroResults = document.getElementById('aeroResults');
    
    const balanceColor = result.balance === 'high_downforce' ? 'var(--accent-color)' : 'var(--warning)';
    
    let html = `
        <div style="background: var(--bg-dark); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="color: ${balanceColor}; margin-bottom: 10px;">
                Setup: ${result.balance.replace('_', ' ').toUpperCase()}
            </h3>
        </div>
        
        <p><strong>Drag Coefficient:</strong> ${result.drag_coefficient.toFixed(3)}</p>
        <p><strong>Downforce Level:</strong> ${result.downforce_level.toFixed(3)}</p>
        <p><strong>Top Speed Gain:</strong> ${result.top_speed_gain > 0 ? '+' : ''}${result.top_speed_gain.toFixed(1)} km/h</p>
        <p><strong>Corner Speed Gain:</strong> ${result.corner_speed_gain > 0 ? '+' : ''}${result.corner_speed_gain.toFixed(1)} km/h</p>
        
        <div style="margin-top: 15px; padding: 10px; background: ${result.lap_time_delta < 0 ? 'rgba(0, 255, 136, 0.1)' : 'rgba(255, 51, 51, 0.1)'}; border-radius: 6px;">
            <strong>Lap Time Impact:</strong> ${result.lap_time_delta > 0 ? '+' : ''}${result.lap_time_delta.toFixed(3)}s
        </div>
    `;
    
    aeroResults.innerHTML = html;
}

// Update Performance Metrics
function updatePerformanceMetrics(simulationResults) {
    document.getElementById('simTime').textContent = (simulationResults.processing_time * 1000).toFixed(0);
    document.getElementById('strategiesEval').textContent = simulationResults.strategies_evaluated;
    document.getElementById('optimalTime').textContent = simulationResults.results[0].total_time.toFixed(1);
    
    if (simulationResults.results.length > 1) {
        const timeSaved = simulationResults.results[1].time_delta;
        document.getElementById('timeSaved').textContent = timeSaved.toFixed(1);
    }
}

// Initialize on load
window.addEventListener('load', () => {
    console.log('F1 Race Decision System initialized');
    
    // Check API health
    fetch(`${API_BASE_URL}/health`)
        .then(response => response.json())
        .then(data => {
            console.log('API Status:', data);
        })
        .catch(error => {
            console.error('API connection failed:', error);
        });
});
