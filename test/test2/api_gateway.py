# 2. API Gateway (중간 계층) - api_gateway.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import sqlite3
import json

gateway_app = Flask(__name__)
CORS(gateway_app)

# Discovery Service URL
DISCOVERY_SERVICE_URL = 'http://localhost:9000'

# 데이터베이스 초기화
def init_gateway_db():
    conn = sqlite3.connect('dspm_gateway.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT UNIQUE,
            asset_type TEXT,
            name TEXT,
            region TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT UNIQUE,
            status TEXT,
            provider TEXT,
            region TEXT,
            assets_found INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@gateway_app.route('/api/scan/start', methods=['POST'])
def start_scan():
    try:
        data = request.get_json()
        
        # Discovery Service에 스캔 요청 전달
        response = requests.post(f'{DISCOVERY_SERVICE_URL}/discover', json=data)
        
        if response.status_code == 200:
            result = response.json()
            
            # 스캔 작업 데이터베이스에 기록
            conn = sqlite3.connect('dspm_gateway.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_jobs (scan_id, status, provider, region)
                VALUES (?, 'started', ?, ?)
            ''', (result['scan_id'], data.get('provider'), data.get('region')))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'scan_id': result['scan_id']})
        else:
            return jsonify({'success': False, 'error': 'Discovery service error'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@gateway_app.route('/api/assets/stats')
def get_asset_stats():
    try:
        conn = sqlite3.connect('dspm_gateway.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM assets')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT asset_type, COUNT(*) FROM assets GROUP BY asset_type')
        type_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'total': total,
            's3_buckets': type_counts.get('S3 Bucket', 0),
            'rds_instances': type_counts.get('RDS Instance', 0),
            'ec2_instances': type_counts.get('EC2 Instance', 0)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@gateway_app.route('/api/assets/list')
def get_asset_list():
    try:
        conn = sqlite3.connect('dspm_gateway.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT asset_id, asset_type, name, region, metadata
            FROM assets
            ORDER BY updated_at DESC
            LIMIT 50
        ''')
        
        assets = []
        for row in cursor.fetchall():
            assets.append({
                'asset_id': row[0],
                'asset_type': row[1],
                'name': row[2],
                'region': row[3],
                'metadata': json.loads(row[4]) if row[4] else {}
            })
        
        conn.close()
        return jsonify({'assets': assets})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@gateway_app.route('/api/assets/save', methods=['POST'])
def save_assets():
    """Discovery Service에서 발견된 자산 저장"""
    try:
        data = request.get_json()
        assets = data.get('assets', [])
        
        conn = sqlite3.connect('dspm_gateway.db')
        cursor = conn.cursor()
        
        for asset in assets:
            cursor.execute('''
                INSERT OR REPLACE INTO assets 
                (asset_id, asset_type, name, region, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                asset['asset_id'],
                asset['asset_type'],
                asset['name'],
                asset['region'],
                json.dumps(asset.get('metadata', {}))
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'saved_count': len(assets)})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    init_gateway_db()
    gateway_app.run(host='0.0.0.0', port=8000, debug=True)