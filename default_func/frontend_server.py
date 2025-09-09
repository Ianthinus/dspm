# 1. Frontend Server (뷰 전용) - frontend_server.py
from flask import Flask, render_template_string
import requests

frontend_app = Flask(__name__)

FRONTEND_HTML = """
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
        .btn { padding: 0.5rem 1rem; margin: 0.25rem; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #3b82f6; color: white; }
        .form-group { margin-bottom: 1rem; }
        .form-input { width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; }
        .scan-controls { margin-bottom: 2rem; padding: 1rem; background: white; border-radius: 8px; }
        .asset-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        .asset-table th, .asset-table td { padding: 0.5rem; text-align: left; border-bottom: 1px solid #e5e7eb; }
        .asset-table th { background: #f9fafb; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Data Security Posture Management</h1>
    </div>
    
    <div class="container">
        <!-- 스캔 컨트롤 -->
        <div class="scan-controls">
            <h3>AWS 자산 발견</h3>
            <div class="form-group">
                <label>AWS Access Key:</label>
                <input type="text" id="accessKey" class="form-input" placeholder="AKIA...">
            </div>
            <div class="form-group">
                <label>AWS Secret Key:</label>
                <input type="password" id="secretKey" class="form-input">
            </div>
            <div class="form-group">
                <label>Region:</label>
                <select id="region" class="form-input">
                    <option value="ap-northeast-2" selected>ap-northeast-2 (Seoul)</option>
                    <option value="us-east-1">us-east-1</option>
                    <option value="us-west-2">us-west-2</option>
                </select>
            </div>
            <button class="btn btn-primary" onclick="startScan()">AWS 스캔 시작</button>
            <button class="btn btn-primary" onclick="refreshData()">데이터 새로고침</button>
        </div>
        
        <div class="grid">
            <div class="card metric">
                <div class="metric-value" id="totalAssets">0</div>
                <div class="metric-label">Total Assets</div>
            </div>
            
            <div class="card metric">
                <div class="metric-value" id="s3Buckets">0</div>
                <div class="metric-label">S3 Buckets</div>
            </div>
            
            <div class="card metric">
                <div class="metric-value" id="rdsInstances">0</div>
                <div class="metric-label">RDS Instances</div>
            </div>
            
            <div class="card">
                <h3>발견된 자산 목록</h3>
                <div style="max-height: 300px; overflow-y: auto;">
                    <table class="asset-table">
                        <thead>
                            <tr>
                                <th>이름</th>
                                <th>유형</th>
                                <th>리전</th>
                                <th>상태</th>
                            </tr>
                        </thead>
                        <tbody id="assetTableBody">
                            <tr><td colspan="4">데이터를 불러오는 중...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // API Gateway 주소 설정
        const API_BASE_URL = 'http://localhost:8000/api';
        
        // 페이지 로드 시 데이터 로드
        document.addEventListener('DOMContentLoaded', refreshData);
        
        function startScan() {
            const accessKey = document.getElementById('accessKey').value;
            const secretKey = document.getElementById('secretKey').value;
            const region = document.getElementById('region').value;
            
            if (!accessKey || !secretKey) {
                alert('AWS 자격 증명을 입력해주세요.');
                return;
            }
            
            fetch(`${API_BASE_URL}/scan/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'aws',
                    credentials: { access_key: accessKey, secret_key: secretKey },
                    region: region
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('스캔이 시작되었습니다. 잠시 후 새로고침해주세요.');
                    setTimeout(refreshData, 5000);
                } else {
                    alert('스캔 시작 실패: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('스캔 요청 실패');
            });
        }
        
        function refreshData() {
            // 자산 통계 로드
            fetch(`${API_BASE_URL}/assets/stats`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalAssets').textContent = data.total || 0;
                    document.getElementById('s3Buckets').textContent = data.s3_buckets || 0;
                    document.getElementById('rdsInstances').textContent = data.rds_instances || 0;
                })
                .catch(error => console.error('Stats error:', error));
            
            // 자산 목록 로드
            fetch(`${API_BASE_URL}/assets/list`)
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('assetTableBody');
                    if (data.assets && data.assets.length > 0) {
                        tbody.innerHTML = data.assets.map(asset => 
                            `<tr>
                                <td>${asset.name}</td>
                                <td>${asset.asset_type}</td>
                                <td>${asset.region}</td>
                                <td>활성</td>
                            </tr>`
                        ).join('');
                    } else {
                        tbody.innerHTML = '<tr><td colspan="4">발견된 자산이 없습니다.</td></tr>';
                    }
                })
                .catch(error => console.error('Assets error:', error));
        }
    </script>
</body>
</html>
"""

@frontend_app.route('/')
def dashboard():
    return render_template_string(FRONTEND_HTML)

if __name__ == '__main__':
    frontend_app.run(host='0.0.0.0', port=5000, debug=True)