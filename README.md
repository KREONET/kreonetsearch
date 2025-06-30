# kreonetsearch
This program for gathering Linux server hardware information

```bash
bash run_all_hw_bash_only.sh
become password: insert sudo password
```

# 유의사항

## pubkey를 이용한  접속
`inventory.ini`의 `(ip changeme)'에 적절한 ip를 입력한다.
`inventory.ini`의 `ansible_user`에 해당 ip의 적절한 USER ID를 입력한다.
`inventory.ini`의 `ansible_ssh_private_key_file`에 프로그램을 실행하는 PC의 pubkey 경로를 입력한다.

## 유저 로그인 후 SU 권한을 얻어 접속
`inventory.ini`의 `(ip changeme)`에 적절한 ip를 입력한다.
`inventory.ini`의 `ansible_user`에 해당 ip의 적절한 USER ID를 입력한다.
`inventory.ini`의 `ansible_password`에 해당 ip의 적절한 USER Password를 입력한다.
`inventory.ini`의 `ansible_become_pass`에 해당 ip의 적절한 Sudo Password를 입력한다.

## 보고서 확인
보고서는 Html과 yaml 파일 형식으로 두개 만들어진다.
Html은 자동으로 웹브라우저에서 열리지만 yaml파일은 수동으로 열어야한다.
