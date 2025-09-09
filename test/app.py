from flask import Flask, render_template_string

app = Flask(__name__)

# HTML 템플릿을 문자열로 직접 포함
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>DSPM Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
        .header { background: #1e293b; color: white; padding: 1rem; text-align: center; }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
        .card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { text-align: center; }
        .metric-value { font-size: 2rem; font-weight: bold; color: #3b82f6; }
        .metric-label { color: #6b7280; margin-top: 0.5rem; }
        .chart-container { height: 300px; margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Data Security Posture Management</h1>
    </div>
    
    <div class="container">
        <div class="grid">
            <div class="card metric">
                <div class="metric-value">1,247</div>
                <div class="metric-label">Total Assets</div>
            </div>
            
            <div class="card metric">
                <div class="metric-value">79%</div>
                <div class="metric-label">Security Score</div>
            </div>
            
            <div class="card metric">
                <div class="metric-value">23</div>
                <div class="metric-label">High Risk Issues</div>
            </div>
            
            <div class="card">
                <h3>Asset Distribution</h3>
                <div class="chart-container">
                    <canvas id="assetChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>Risk Trends</h3>
                <div class="chart-container">
                    <canvas id="riskChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>Recent Scans</h3>
                <ul>
                    <li>AWS S3 Scan - Completed</li>
                    <li>Database Scan - In Progress</li>
                    <li>File Share Scan - Pending</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        // Asset Distribution Chart
        const assetCtx = document.getElementById('assetChart').getContext('2d');
        new Chart(assetCtx, {
            type: 'doughnut',
            data: {
                labels: ['S3 Buckets', 'Databases', 'Files'],
                datasets: [{
                    data: [45, 30, 25],
                    backgroundColor: ['#3b82f6', '#ef4444', '#10b981']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });

        // Risk Trends Chart
        const riskCtx = document.getElementById('riskChart').getContext('2d');
        new Chart(riskCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
                datasets: [{
                    label: 'High Risk',
                    data: [12, 19, 15, 25, 23],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)