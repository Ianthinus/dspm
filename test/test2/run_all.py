import subprocess
import time
import os

def run_service(script_name, port, service_name):
    """개별 서비스 실행"""
    print(f"Starting {service_name} on port {port}...")
    return subprocess.Popen(['python3', script_name])

if __name__ == '__main__':
    processes = []
    
    try:
        # Discovery Service 시작 (포트 9000)
        processes.append(run_service('discovery_service.py', 9001, 'Discovery Service'))
        time.sleep(2)
        
        # API Gateway 시작 (포트 8000)
        processes.append(run_service('api_gateway.py', 8000, 'API Gateway'))
        time.sleep(2)
        
        # Frontend Server 시작 (포트 5000)
        processes.append(run_service('frontend_server.py', 5000, 'Frontend Server'))
        
        print("\n모든 서비스가 시작되었습니다:")
        print("- Frontend: http://localhost:5000")
        print("- API Gateway: http://localhost:8000")
        print("- Discovery Service: http://localhost:9000")
        print("\nCtrl+C로 모든 서비스를 종료할 수 있습니다.")
        
        # 모든 프로세스가 종료될 때까지 대기
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n서비스를 종료하는 중...")
        for process in processes:
            process.terminate()
        print("모든 서비스가 종료되었습니다.")