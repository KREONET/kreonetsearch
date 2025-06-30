import os
import sys
import re
try:
    import yaml # YAML 파일 생성을 위해 PyYAML 라이브러리 import
except ImportError:
    print("오류: PyYAML 라이브러리를 찾을 수 없습니다.")
    print("YAML 보고서를 생성하려면 'pip install PyYAML' 명령으로 설치해야 합니다.")
    sys.exit(1) # PyYAML 없으면 스크립트 종료

# Raw 데이터 파일들이 저장될 기본 디렉토리를 정의합니다.
FETCHED_HW_DATA_DIR = "./fetched_hw_data/"
# 생성될 보고서 파일들을 저장할 디렉토리를 정의합니다.
RESULT_DIR = "./result/" # <--- 새로운 결과 디렉토리 정의

# 생성될 보고서 파일의 경로를 정의합니다.
# os.path.join을 사용하여 디렉토리와 파일 이름을 결합합니다.
HTML_REPORT_FILE = os.path.join(RESULT_DIR, "hardware_inventory_report_bash_only.html")
YAML_REPORT_FILE = os.path.join(RESULT_DIR, "hardware_inventory_report_bash_only.yaml")

def parse_inventory_hosts(inventory_file):
    """
    inventory.ini 파일에서 [servers] 그룹과 [local] 그룹을 포함한 모든 호스트 이름을 파싱합니다.
    """
    hosts = []
    current_group_type = None
    try:
        with open(inventory_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                group_match = re.match(r'\[(?P<group_name>[\w.-]+)\]', line)
                if group_match:
                    group_name = group_match.group('group_name')
                    if group_name == 'servers':
                        current_group_type = 'servers'
                    elif group_name == 'local':
                        current_group_type = 'local'
                    else:
                        current_group_type = None
                    continue

                if current_group_type in ['servers', 'local']:
                    # 호스트명 또는 IP 주소만 추출 (변수 부분은 무시)
                    match = re.match(r'^(?P<hostname_or_ip>[\w.-]+)', line)
                    if match:
                        hosts.append(match.group('hostname_or_ip'))
    except FileNotFoundError:
        print(f"오류: 인벤토리 파일 '{inventory_file}'를 찾을 수 없습니다. 호스트 목록을 가져올 수 없습니다.")
    except Exception as e:
        print(f"인벤토리 파일 파싱 중 오류 발생: {e}")
    return list(set(hosts)) # 중복 제거

def parse_raw_hw_data(file_path):
    """
    Bash 스크립트에서 수집된 raw 하드웨어 데이터를 파싱합니다.
    """
    hw_data = {
        'hostname': 'N/A', # 파일에서 파싱될 호스트명
        'status': 'Collected', # 데이터 수집 성공 상태 (초기값)
        'ip_addresses': ['N/A'],
        'cpu': {'model': 'N/A', 'logical_cpus': 'N/A', 'cores_per_socket': 'N/A', 'threads_per_core': 'N/A'},
        'system_info': {'manufacturer': 'N/A', 'product_name': 'N/A', 'serial_number': 'N/A', 'version': 'N/A'},
        'mainboard': {'manufacturer': 'N/A', 'product': 'N/A', 'serial': 'N/A', 'version': 'N/A'},
        'bios': {'vendor': 'N/A', 'version': 'N/A'},
        'os': {'distribution': 'N/A', 'version': 'N/A', 'kernel': 'N/A'},
        'memory_mb': 'N/A'
    }
    
    current_section = None
    lines_in_section = [] # 현재 섹션의 모든 줄을 저장

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 호스트명 먼저 파싱
        if lines and lines[0].startswith('---HOST:'):
            hw_data['hostname'] = lines[0].split(':', 1)[1].strip().rstrip('---')
            lines = lines[1:] # 호스트명 줄 제거
        else:
            print(f"경고: 파일 '{file_path}'에서 '---HOST:' 구분자를 찾을 수 없거나 형식이 잘못되었습니다. 호스트명은 'N/A'로 표시됩니다.")
            
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('---SECTION:'):
                if current_section: # 이전 섹션 데이터 처리
                    if current_section == 'IP_ADDRESSES':
                        if lines_in_section and lines_in_section[0] != "N/A": hw_data['ip_addresses'] = lines_in_section[0].split()
                    elif current_section == 'CPU':
                        if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['cpu']['model'] = lines_in_section[0]
                        if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['cpu']['logical_cpus'] = lines_in_section[1]
                        if len(lines_in_section) >= 3 and lines_in_section[2] != "N/A": hw_data['cpu']['cores_per_socket'] = lines_in_section[2]
                        if len(lines_in_section) >= 4 and lines_in_section[3] != "N/A": hw_data['cpu']['threads_per_core'] = lines_in_section[3]
                    elif current_section == 'SYSTEM_INFO':
                        if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['system_info']['manufacturer'] = lines_in_section[0]
                        if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['system_info']['product_name'] = lines_in_section[1]
                        if len(lines_in_section) >= 3 and lines_in_section[2] != "N/A": hw_data['system_info']['serial_number'] = lines_in_section[2]
                        if len(lines_in_section) >= 4 and lines_in_section[3] != "N/A": hw_data['system_info']['version'] = lines_in_section[3]
                    elif current_section == 'MAINBOARD':
                        if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['mainboard']['manufacturer'] = lines_in_section[0]
                        if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['mainboard']['product'] = lines_in_section[1]
                        if len(lines_in_section) >= 3 and lines_in_section[2] != "N/A": hw_data['mainboard']['serial'] = lines_in_section[2]
                        if len(lines_in_section) >= 4 and lines_in_section[3] != "N/A": hw_data['mainboard']['version'] = lines_in_section[3]
                    elif current_section == 'BIOS':
                        if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['bios']['vendor'] = lines_in_section[0]
                        if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['bios']['version'] = lines_in_section[1]
                    elif current_section == 'OS_INFO':
                        if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['os']['distribution'] = lines_in_section[0]
                        if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['os']['version'] = lines_in_section[1]
                        if len(lines_in_section) >= 3 and lines_in_section[2] != "N/A": hw_data['os']['kernel'] = lines_in_section[2]
                    elif current_section == 'MEMORY':
                        if lines_in_section and lines_in_section[0] != "N/A": hw_data['memory_mb'] = lines_in_section[0]
                
                current_section = line.split(':', 1)[1].rstrip('---')
                lines_in_section = [] # 새 섹션 시작, 리스트 초기화
            elif line:
                lines_in_section.append(line)
            
            i += 1
        
        # 파일의 마지막 섹션 처리
        if current_section:
            if current_section == 'IP_ADDRESSES':
                if lines_in_section and lines_in_section[0] != "N/A": hw_data['ip_addresses'] = lines_in_section[0].split()
            elif current_section == 'CPU':
                if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['cpu']['model'] = lines_in_section[0]
                if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['cpu']['logical_cpus'] = lines_in_section[1]
                if len(lines_in_section) >= 3 and lines_in_section[2] != "N/A": hw_data['cpu']['cores_per_socket'] = lines_in_section[2]
                if len(lines_in_section) >= 4 and lines_in_section[3] != "N/A": hw_data['cpu']['threads_per_core'] = lines_in_section[3]
            elif current_section == 'SYSTEM_INFO':
                if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['system_info']['manufacturer'] = lines_in_section[0]
                if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['system_info']['product_name'] = lines_in_section[1]
                if len(lines_in_section) >= 3 and lines_in_section[2] != "N/A": hw_data['system_info']['serial_number'] = lines_in_section[2]
                if len(lines_in_section) >= 4 and lines_in_section[3] != "N/A": hw_data['system_info']['version'] = lines_in_section[3]
            elif current_section == 'MAINBOARD':
                if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['mainboard']['manufacturer'] = lines_in_section[0]
                if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['mainboard']['product'] = lines_in_section[1]
                if len(lines_in_section) >= 3 and lines_in_section[2] != "N/A": hw_data['mainboard']['serial'] = lines_in_section[2]
                if len(lines_in_section) >= 4 and lines_in_section[3] != "N/A": hw_data['mainboard']['version'] = lines_in_section[3]
            elif current_section == 'BIOS':
                if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['bios']['vendor'] = lines_in_section[0]
                if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['bios']['version'] = lines_in_section[1]
            elif current_section == 'OS_INFO':
                if len(lines_in_section) >= 1 and lines_in_section[0] != "N/A": hw_data['os']['distribution'] = lines_in_section[0]
                if len(lines_in_section) >= 2 and lines_in_section[1] != "N/A": hw_data['os']['version'] = lines_in_section[1]
                if len(lines_in_section) >= 3 and lines_in_section[2] != "N/A": hw_data['os']['kernel'] = lines_in_section[2]
            elif current_section == 'MEMORY':
                if lines_in_section: hw_data['memory_mb'] = lines_in_section[0]

    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
        hw_data['status'] = 'File Not Found'
    except Exception as e:
        print(f"파일을 읽거나 파싱하는 중 오류가 발생했습니다: '{file_path}': {e}")
        hw_data['status'] = f'Parsing Error: {e}'
    return hw_data

def parse_all_hw_data_files(base_dir, inventory_file):
    """
    inventory.ini의 모든 호스트 목록을 가져와
    각 호스트의 Raw 데이터 파일을 읽고 파싱하거나, 실패 상태를 표시합니다.
    """
    all_hosts_hw_data = {}
    
    # 1. inventory.ini에서 모든 호스트 목록 가져오기
    all_target_hosts = parse_inventory_hosts(inventory_file)
    if not all_target_hosts:
        print(f"오류: 인벤토리 파일 '{inventory_file}'에서 대상 호스트를 찾을 수 없습니다. 보고서가 생성되지 않습니다.")
        return all_hosts_hw_data

    # 2. 각 호스트에 대한 기본 '수집 실패' 엔트리 초기화
    for host in all_target_hosts:
        all_hosts_hw_data[host] = {
            'hostname': host,
            'status': 'Collection Failed',
            'ip_addresses': ['N/A'],
            'cpu': {'model': 'N/A', 'logical_cpus': 'N/A', 'cores_per_socket': 'N/A', 'threads_per_core': 'N/A'},
            'system_info': {'manufacturer': 'N/A', 'product_name': 'N/A', 'serial_number': 'N/A', 'version': 'N/A'},
            'mainboard': {'manufacturer': 'N/A', 'product': 'N/A', 'serial': 'N/A', 'version': 'N/A'},
            'bios': {'vendor': 'N/A', 'version': 'N/A'},
            'os': {'distribution': 'N/A', 'version': 'N/A', 'kernel': 'N/A'},
            'memory_mb': 'N/A'
        }

    # 3. fetched_hw_data 디렉토리가 존재하는지 확인
    if not os.path.exists(base_dir):
        print(f"경고: 데이터 수집 디렉토리 '{base_dir}'를 찾을 수 없습니다. 모든 호스트는 '수집 실패'로 표시됩니다.")
        return all_hosts_hw_data

    # 4. 수집된 Raw 데이터 파일 파싱 및 성공한 호스트 정보 업데이트
    for host_in_inventory in all_target_hosts:
        filename = f"{host_in_inventory}_raw_hw.txt"
        file_path = os.path.join(base_dir, filename)

        if os.path.exists(file_path):
            print(f"\n호스트 '{host_in_inventory}'의 하드웨어 정보 파싱 시도 중: {file_path}")
            data = parse_raw_hw_data(file_path)
            
            # 파일 내부에서 파싱된 호스트명이 있다면 사용, 없다면 인벤토리 호스트명을 사용
            actual_hostname_in_file = data.get('hostname', 'N/A')
            if actual_hostname_in_file == 'N/A' or actual_hostname_in_file == '':
                data['hostname'] = host_in_inventory # 파싱 실패 시 인벤토리 호스트명 사용

            # ---HOST: 라인을 성공적으로 파싱하고, 내용도 유의미하면 'Collected' 상태로 업데이트
            # 유효한 IP 주소나 CPU 모델이 하나라도 있으면 성공으로 간주
            if data['hostname'] != 'N/A' and (data['ip_addresses'] != ['N/A'] or data['cpu']['model'] != 'N/A' or data['system_info']['manufacturer'] != 'N/A'):
                data['status'] = 'Collected'
                print(f"-> 호스트 '{data['hostname']}' 데이터 파싱 성공. HTML 보고서에 포함됩니다.")
            else:
                data['status'] = 'Parsing Failed / No Data'
                print(f"-> 경고: 호스트 '{host_in_inventory}'의 데이터 파싱 실패 또는 유의미한 데이터 부족. HTML 보고서에 'Parsing Failed'로 표시됩니다.")
                print(f"    (파일 '{file_path}'의 '---HOST:' 라인과 내용 형식을 확인하세요.)")
                
            all_hosts_hw_data[host_in_inventory] = data
        else:
            # 파일이 존재하지 않는 경우 (Ansible 수집 실패)
            print(f"\n호스트 '{host_in_inventory}'의 Raw 데이터 파일이 존재하지 않습니다: {file_path}")
            all_hosts_hw_data[host_in_inventory]['status'] = 'Collection Failed'
            print(f"-> 호스트 '{host_in_inventory}' 데이터 수집 실패. HTML 보고서에 'Collection Failed'로 표시됩니다.")

    return all_hosts_hw_data

def generate_html_report(all_hosts_hw_data, output_file):
    """
    모든 호스트의 하드웨어 데이터를 기반으로 HTML 보고서를 생성합니다.
    """
    # 결과 디렉토리가 없으면 생성
    os.makedirs(RESULT_DIR, exist_ok=True) # <--- 디렉토리 생성 추가

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>하드웨어 자산 보고서 (Bash 전용)</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            font-family: "Inter", sans-serif;
            background-color: #f3f4f6;
            color: #374151;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 0.5rem; /* rounded-lg */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-lg */
            padding: 2rem; /* p-8 */
            width: 100%;
            max-width: 1200px; /* max-w-4xl */
        }}
        .host-section {{
            margin-bottom: 2.5rem; /* mb-10 */
            border: 1px solid #e5e7eb; /* border-gray-200 */
            border-radius: 0.375rem; /* rounded-md */
            padding: 1.5rem; /* p-6 */
            background-color: #ffffff;
        }}
        .host-section.failed {{
            border-color: #ef4444; /* Red for failed */
            background-color: #fee2e2; /* Light red background */
        }}
        .host-section.parsing-failed {{
            border-color: #f59e0b; /* Amber for parsing issues */
            background-color: #fffbeb; /* Light yellow background */
        }}
        .host-section h2 {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .host-section h2 .status {{
            font-size: 0.875rem; /* text-sm */
            font-weight: 700; /* font-bold */
            padding: 0.25rem 0.5rem; /* px-2 py-1 */
            border-radius: 0.25rem; /* rounded */
            color: #ffffff;
        }}
        .host-section h2 .status.collected {{
            background-color: #10b981; /* Green */
        }}
        .host-section h2 .status.failed {{
            background-color: #ef4444; /* Red */
        }}
        .host-section h2 .status.parsing-failed {{
            background-color: #f59e0b; /* Amber */
        }}

        .host-section:not(:last-child) {{
            margin-bottom: 2rem;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem; /* gap-6 */
            margin-top: 1.5rem; /* mt-6 */
        }}
        .info-card {{
            background-color: #f9fafb; /* bg-gray-50 */
            border-radius: 0.375rem; /* rounded-md */
            padding: 1rem; /* p-4 */
            border: 1px solid #e5e7eb; /* border-gray-200 */
        }}
        .info-card h3 {{
            font-weight: 600; /* font-semibold */
            color: #1f2937; /* text-gray-900 */
            margin-bottom: 0.5rem; /* mb-2 */
        }}
        .info-card p {{
            color: #4b5563; /* text-gray-700 */
            font-size: 0.875rem; /* text-sm */
        }}
        .info-card p strong {{
            color: #1f2937; /* text-gray-900 */
        }}
    </style>
</head>
<body class="bg-gray-100 p-4 sm:p-6 lg:p-8">
    <div class="container mx-auto rounded-lg shadow-lg p-6 sm:p-8 lg:p-10">
        <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 mb-6 text-center">하드웨어 자산 보고서 (Bash 전용)</h1>
        
        <p class="text-gray-700 mb-8 text-center">
            이 보고서는 원격 서버에 Python 인터프리터가 필요 없이 Bash 명령어를 통해서 수집된 하드웨어 자산 정보를 표시합니다.
            CPU, IP 주소, 메인보드, 시스템 벤더, OS 및 메모리 정보가 포함됩니다.
        </p>
    """

    if not all_hosts_hw_data:
        html_content += """
        <div class="text-center text-gray-600 text-lg py-10 rounded-md bg-white border border-gray-200 p-6">
            <p>보고서를 생성할 데이터가 없습니다. Ansible 플레이북 실행 결과를 확인하세요。</p>
        </div>
        """
    else:
        # 호스트 이름을 알파벳 순으로 정렬하여 출력합니다.
        for hostname_from_file in sorted(all_hosts_hw_data.keys()):
            hw = all_hosts_hw_data[hostname_from_file]
            
            # 상태에 따른 CSS 클래스 결정
            section_class = "host-section"
            status_class = "collected" # 기본값
            if hw.get('status') == 'Collection Failed':
                section_class += " failed"
                status_class = "failed"
            elif hw.get('status') == 'Parsing Failed / No Data':
                section_class += " parsing-failed"
                status_class = "parsing-failed"

            html_content += f"""
        <div class="{section_class} rounded-md shadow-sm">
            <h2 class="text-xl sm:text-2xl font-semibold text-gray-800 mb-4">
                호스트: <span class="text-indigo-600 break-all">{hostname_from_file}</span>
                <span class="status {status_class}">{hw.get('status', 'Unknown')}</span>
            </h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>시스템 정보</h3>
                    <p><strong>호스트명:</strong> {hw.get('hostname', 'N/A')}</p>
                    <p><strong>시스템 벤더:</strong> {hw['system_info'].get('manufacturer', 'N/A')}</p>
                    <p><strong>제품명:</strong> {hw['system_info'].get('product_name', 'N/A')}</p>
                    <p><strong>세부 모델/버전:</strong> {hw['system_info'].get('version', 'N/A')}</p>
                    <p><strong>시리얼 번호:</strong> {hw['system_info'].get('serial_number', 'N/A')}</p>
                </div>
                <div class="info-card">
                    <h3>CPU 정보</h3>
                    <p><strong>모델:</strong> {hw['cpu'].get('model', 'N/A')}</p>
                    <p><strong>논리 CPU 수:</strong> {hw['cpu'].get('logical_cpus', 'N/A')}</p>
                    <p><strong>소켓당 코어 수:</strong> {hw['cpu'].get('cores_per_socket', 'N/A')}</p>
                    <p><strong>코어당 스레드 수:</strong> {hw['cpu'].get('threads_per_core', 'N/A')}</p>
                </div>
                <div class="info-card">
                    <h3>네트워크 정보</h3>
                    <p><strong>IP 주소:</strong> {', '.join(hw.get('ip_addresses', ['N/A']))}</p>
                </div>
                <div class="info-card">
                    <h3>메인보드 정보</h3>
                    <p><strong>제조사:</strong> {hw['mainboard'].get('manufacturer', 'N/A')}</p>
                    <p><strong>제품명:</strong> {hw['mainboard'].get('product', 'N/A')}</p>
                    <p><strong>시리얼:</strong> {hw['mainboard'].get('serial', 'N/A')}</p>
                    <p><strong>버전:</strong> {hw['mainboard'].get('version', 'N/A')}</p>
                </div>
                <div class="info-card">
                    <h3>BIOS 정보</h3>
                    <p><strong>벤더:</strong> {hw['bios'].get('vendor', 'N/A')}</p>
                    <p><strong>버전:</strong> {hw['bios'].get('version', 'N/A')}</p>
                </div>
                <div class="info-card">
                    <h3>OS 및 메모리</h3>
                    <p><strong>배포판:</strong> {hw['os'].get('distribution', 'N/A')}</p>
                    <p><strong>버전:</strong> {hw['os'].get('version', 'N/A')}</p>
                    <p><strong>커널:</strong> {hw['os'].get('kernel', 'N/A')}</p>
                    <p><strong>총 메모리:</strong> {hw.get('memory_mb', 'N/A')} MB</p>
                </div>
            </div>
        </div>
            """

    html_content += """
    </div>
</body>
</html>
    """

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML 보고서가 성공적으로 생성되었습니다: {output_file}")
    except Exception as e:
        print(f"HTML 보고서 생성 중 오류가 발생했습니다: {e}")

def generate_yaml_report(all_hosts_hw_data, output_file):
    """
    모든 호스트의 하드웨어 데이터를 기반으로 YAML 보고서를 생성합니다.
    실패한 호스트는 YAML 보고서에서 제외됩니다.
    """
    # 결과 디렉토리가 없으면 생성
    os.makedirs(RESULT_DIR, exist_ok=True) # <--- 디렉토리 생성 추가

    print(f"YAML 보고서 생성 중: {output_file}")
    filtered_data_for_yaml = {}
    for hostname, data in all_hosts_hw_data.items():
        if data.get('status') == 'Collected': # 'Collected' 상태인 호스트만 포함
            clean_data = data.copy()
            clean_data.pop('status', None) 
            filtered_data_for_yaml[hostname] = clean_data
        else:
            print(f"정보: 호스트 '{hostname}'은(는) 수집 실패 또는 파싱 실패 상태이므로 YAML 보고서에서 제외됩니다.")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(filtered_data_for_yaml, f, default_flow_style=False, allow_unicode=True, indent=2, width=80, sort_keys=False)
        print(f"YAML 보고서가 성공적으로 생성되었습니다: {output_file}")
    except Exception as e:
        print(f"오류: YAML 보고서 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python process_hw_info_bash_only.py <inventory_file>")
        sys.exit(1)
    
    inventory_file_path = sys.argv[1]
    
    print("Python 스크립트 실행 중...")
    
    # 모든 호스트의 하드웨어 정보 파싱
    all_hosts_hw_data = parse_all_hw_data_files(FETCHED_HW_DATA_DIR, inventory_file_path)

    # HTML 보고서 생성
    generate_html_report(all_hosts_hw_data, HTML_REPORT_FILE)
    
    # YAML 보고서 생성
    generate_yaml_report(all_hosts_hw_data, YAML_REPORT_FILE)
    
    print("\n--- 다음 단계를 진행하세요 ---")
    print(f"HTML 보고서가 생성되었습니다: {HTML_REPORT_FILE}")
    print(f"YAML 보고서가 생성되었습니다: {YAML_REPORT_FILE}")
    print("이 파일을 웹 브라우저에서 열어 내용을 확인할 수 있습니다.")
