# 3. Discovery Service (스캔 전용) - discovery_service.py
from flask import Flask, request, jsonify
import boto3
import json
import requests
from datetime import datetime
import threading

discovery_app = Flask(__name__)

class AWSDiscoveryService:
    def __init__(self, access_key, secret_key, region='us-east-1'):
        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        self.region = region
        self.assets = []
    
    def discover_all(self):
        """모든 AWS 자산 발견"""
        try:
            self.discover_s3_buckets()
            self.discover_rds_instances()
            self.discover_ec2_instances()
            return self.assets
        except Exception as e:
            raise Exception(f"AWS 발견 실패: {str(e)}")
    
    # discovery_service.py의 수정된 discover_s3_buckets 메서드

    def discover_s3_buckets(self):
        """S3 버킷 및 내부 객체 발견"""
        try:
            s3 = self.session.client('s3')
            buckets = s3.list_buckets()
            
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                
                # 기본 메타데이터
                metadata = {
                    'creation_date': bucket['CreationDate'].isoformat(),
                    'service': 's3'
                }
                
                # 버킷 위치 확인
                try:
                    location = s3.get_bucket_location(Bucket=bucket_name)
                    bucket_region = location.get('LocationConstraint') or 'us-east-1'
                    metadata['region'] = bucket_region
                except:
                    metadata['region'] = 'unknown'
                
                # 퍼블릭 액세스 확인
                try:
                    public_block = s3.get_public_access_block(Bucket=bucket_name)
                    metadata['is_public'] = not all(public_block['PublicAccessBlockConfiguration'].values())
                except:
                    metadata['is_public'] = True
                
                # 버킷 자산 추가
                bucket_asset = {
                    'asset_id': f"s3://{bucket_name}",
                    'asset_type': 'S3 Bucket',
                    'name': bucket_name,
                    'region': metadata.get('region', self.region),
                    'metadata': metadata
                }
                self.assets.append(bucket_asset)
                
                # 버킷 내부 객체들 스캔
                try:
                    self.scan_bucket_objects(s3, bucket_name)
                except Exception as e:
                    print(f"버킷 {bucket_name} 객체 스캔 실패: {e}")
                    
        except Exception as e:
            print(f"S3 스캔 실패: {e}")

    def scan_bucket_objects(self, s3, bucket_name, max_objects=500):
        """S3 버킷 내부 객체들을 개별 자산으로 추가"""
        try:
            response = s3.list_objects_v2(
                Bucket=bucket_name,
                MaxKeys=max_objects
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    size = obj['Size']
                    last_modified = obj['LastModified']
                    
                    # 객체 메타데이터 (단순 식별 정보만)
                    obj_metadata = {
                        'bucket': bucket_name,
                        'key': key,
                        'size_bytes': size,
                        'size_readable': self.format_file_size(size),
                        'last_modified': last_modified.isoformat(),
                        'service': 's3'
                    }
                    
                    # 파일 확장자
                    if '.' in key:
                        obj_metadata['file_extension'] = key.split('.')[-1].lower()
                    
                    # 폴더 경로
                    if '/' in key:
                        obj_metadata['folder_path'] = '/'.join(key.split('/')[:-1])
                        obj_metadata['file_name'] = key.split('/')[-1]
                    else:
                        obj_metadata['file_name'] = key
                    
                    # S3 객체를 개별 자산으로 추가
                    object_asset = {
                        'asset_id': f"s3://{bucket_name}/{key}",
                        'asset_type': 'S3 Object',
                        'name': obj_metadata['file_name'],
                        'region': self.region,
                        'metadata': obj_metadata
                    }
                    
                    self.assets.append(object_asset)
                    
        except Exception as e:
            print(f"객체 스캔 오류: {e}")

    def format_file_size(self, size_bytes):
        """바이트를 읽기 쉬운 형태로 변환"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def discover_rds_instances(self):
        """RDS 인스턴스 발견"""
        try:
            rds = self.session.client('rds')
            instances = rds.describe_db_instances()
            
            for instance in instances['DBInstances']:
                db_id = instance['DBInstanceIdentifier']
                
                metadata = {
                    'engine': instance.get('Engine'),
                    'engine_version': instance.get('EngineVersion'),
                    'instance_class': instance.get('DBInstanceClass'),
                    'status': instance.get('DBInstanceStatus'),
                    'multi_az': instance.get('MultiAZ'),
                    'encrypted': instance.get('StorageEncrypted'),
                    'service': 'rds'
                }
                
                asset = {
                    'asset_id': f"rds://{db_id}",
                    'asset_type': 'RDS Instance',
                    'name': db_id,
                    'region': self.region,
                    'metadata': metadata
                }
                
                self.assets.append(asset)
                
        except Exception as e:
            print(f"RDS 스캔 실패: {e}")
    
    def discover_ec2_instances(self):
        """EC2 인스턴스 발견"""
        try:
            ec2 = self.session.client('ec2')
            instances = ec2.describe_instances()
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    
                    # 이름 태그 찾기
                    name = instance_id
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    metadata = {
                        'instance_type': instance.get('InstanceType'),
                        'state': instance.get('State', {}).get('Name'),
                        'vpc_id': instance.get('VpcId'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'service': 'ec2'
                    }
                    
                    asset = {
                        'asset_id': f"ec2://{instance_id}",
                        'asset_type': 'EC2 Instance', 
                        'name': name,
                        'region': self.region,
                        'metadata': metadata
                    }
                    
                    self.assets.append(asset)
                    
        except Exception as e:
            print(f"EC2 스캔 실패: {e}")

def perform_discovery(provider, credentials, region, scan_id):
    """백그라운드에서 발견 작업 수행"""
    try:
        if provider == 'aws':
            discovery = AWSDiscoveryService(
                credentials['access_key'],
                credentials['secret_key'],
                region
            )
            assets = discovery.discover_all()
            
            # API Gateway에 결과 전송
            response = requests.post('http://localhost:8000/api/assets/save', json={
                'scan_id': scan_id,
                'assets': assets
            })
            
            print(f"스캔 완료: {len(assets)}개 자산 발견")
            
    except Exception as e:
        print(f"발견 작업 실패: {e}")

@discovery_app.route('/discover', methods=['POST'])
def start_discovery():
    """발견 작업 시작"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        credentials = data.get('credentials')
        region = data.get('region', 'ap-northeast-2')  # 서울 리전 기본값
        
        # 스캔 ID 생성
        scan_id = f"scan_{int(datetime.now().timestamp())}"
        
        # 백그라운드에서 발견 작업 실행
        thread = threading.Thread(
            target=perform_discovery,
            args=(provider, credentials, region, scan_id)
        )
        thread.start()
        
        return jsonify({'success': True, 'scan_id': scan_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@discovery_app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'discovery'})

if __name__ == '__main__':
    discovery_app.run(host='0.0.0.0', port=9000, debug=True)