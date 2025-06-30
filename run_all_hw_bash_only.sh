#!/bin/bash

# 사용법: bash run_all_hw_bash_only.sh 또는 ./run_all_hw_bash_only.sh (실행 권한 부여 후)

INVENTORY_FILE="inventory.ini"
ANSIBLE_HW_PLAYBOOK="collect_hw_info_bash_only.yml" # 플레이북 이름
PYTHON_PROCESS_SCRIPT="process_hw_info_bash_only.py" # Python 스크립트 이름
RESULT_DIR="result" # 결과 디렉토리 변수

# HTML 보고서 파일의 경로를 절대 경로로 지정합니다.
# $(pwd)는 현재 작업 디렉토리의 절대 경로를 반환합니다.
HTML_REPORT_FILE="$(pwd)/$RESULT_DIR/hardware_inventory_report_bash_only.html" # <--- 이 줄이 수정되었습니다.

# 함수: 사용자에게 메시지를 표시하고 수동 파일 열기를 안내합니다.
show_manual_open_message() {
    echo -e "\n--------------------------------------------------------------"
    echo "경고: 웹 브라우저에서 HTML 보고서를 자동으로 열 수 없습니다."
    echo "보고서 파일은 여기에 생성되었습니다: $HTML_REPORT_FILE" # 변수 사용
    echo "웹 브라우저를 열고 이 파일을 수동으로 드래그 앤 드롭하거나, 파일 탐색기에서 파일을 클릭하여 여세요."
    echo "--------------------------------------------------------------"
}

# fetched_hw_data 디렉토리 초기화 (이전 실행 결과 제거)
echo "--- 기존 fetched_hw_data 디렉토리 삭제 (선택 사항) ---"
rm -rf fetched_hw_data
mkdir -p fetched_hw_data # 새로운 fetched_hw_data 디렉토리 생성

# result 디렉토리 생성
echo "--- 결과 보고서 디렉토리 생성 ---"
mkdir -p "$RESULT_DIR" # result 디렉토리 생성

echo "--- 하드웨어 자산 보고서 생성 프로세스 시작 (Bash 전용 모드) ---"
echo "경고: SSH 호스트 키 검증이 비활성화됩니다. (StrictHostKeyChecking=no)"

# 1. 원격 서버에서 하드웨어 정보 수집
echo -e "\n[단계 1/2] 원격 서버에서 하드웨어 정보 수집 중..."
# ANSIBLE_BECOME_ASK_PASS=true 환경 변수를 설정하여 Ansible이 sudo/su 비밀번호를 물어보도록 합니다.
ANSIBLE_BECOME_ASK_PASS=true ansible-playbook -i "$INVENTORY_FILE" "$ANSIBLE_HW_PLAYBOOK" --ssh-common-args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'

# Ansible 플레이북 실행 결과($?)를 확인합니다.
ANSIBLE_EXIT_CODE=$?

if [ $ANSIBLE_EXIT_CODE -ne 0 ]; then
    echo "Ansible 플레이북 실행 중 일부 오류가 발생했습니다 (종료 코드: $ANSIBLE_EXIT_CODE)."
    echo "Python 스크립트가 성공 및 실패한 호스트 정보를 처리합니다."
fi

# 2. 가져온 하드웨어 데이터를 기반으로 HTML 보고서 생성
echo -e "\n[단계 2/2] 가져온 하드웨어 데이터를 기반으로 HTML 보고서 생성 중..."

# Python 실행 파일 확인 (python3 우선, 없으면 python 시도)
PYTHON_EXECUTABLE=""
if command -v python3 &> /dev/null; then
    PYTHON_EXECUTABLE="python3"
elif command -v python &> /dev/null; then
    PYTHON_EXECUTABLE="python"
else
    echo "오류: Python 3 또는 Python 실행 파일을 찾을 수 없습니다. Python이 설치되어 있는지 확인하세요."
    exit 1
fi

"$PYTHON_EXECUTABLE" "$PYTHON_PROCESS_SCRIPT" "$INVENTORY_FILE" # 인벤토리 파일 경로를 인자로 전달
if [ $? -ne 0 ]; then
    echo "오류: Python 스크립트 ($PYTHON_PROCESS_SCRIPT) 실행에 실패했습니다. 클라이언트에 Python이 설치되어 있는지 확인하고 PyYAML 라이브러리 설치 여부를 확인하세요."
    exit 1
fi

# 3. HTML 보고서 웹 브라우저로 열기
echo -e "\n--- HTML 보고서 열기: $HTML_REPORT_FILE ---"
OPEN_SUCCESS=0

if [[ "$OSTYPE" == "darwin"* ]]; then # macOS
    open "$HTML_REPORT_FILE" && OPEN_SUCCESS=1
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then # Linux
    xdg-open "$HTML_REPORT_FILE" && OPEN_SUCCESS=1
elif [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then # Windows (Git Bash, WSL 등)
    cmd.exe /C start "$HTML_REPORT_FILE" && OPEN_SUCCESS=1
fi

# 만약 자동으로 열리지 않았다면, 수동으로 열도록 안내 메시지를 표시합니다.
if [ "$OPEN_SUCCESS" -eq 0 ]; then
    show_manual_open_message
else
    echo "웹 브라우저에서 보고서를 열었습니다."
fi

echo -e "\n--- 하드웨어 자산 보고서 생성 프로세스 완료 ---"
