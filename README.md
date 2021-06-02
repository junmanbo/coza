# coza

Auto Trading  
내가 **"코~ 자는 동안"** 돈 벌어다 주는 트레이딩 봇

## 설명(explanation)

- 본 전략은 데이트레이딩 전략으로 초단타 매매를 진행합니다.
- 바이낸스 거래소를 이용하며 선물 거래를 기본으로 하여 레버리지 설정 및 (롱/숏) 포지션 거래가 가능합니다. (API 필요)
- 거래 진행시, 에러 발생시 텔레그램으로 정보를 전송합니다. (API 필요)
- 거래에 대한 정보, 또는 프로그램내의 진행 상황을 로그로 남겨 놓습니다. (Log/trading.log)
- 하루동안의 거래내역 (투자금액 및 수익률)을 엑셀파일로 기록합니다. (Data/trading.xlsx)
- 코인에 대한 각종 정보들 (코인별 매수/매도 가격, 포지션 상태)을 저장합니다. (Data/trading.txt)
- 하루에 한 번씩 (KST 기준 9시) 상승/하락 추세를 판단하여 상승장(Bull)일 경우 롱 포지션을 하락장(Bear)일 경우 숏 포지션을 취합니다.
- 30분 마다 가격을 체크하여 거래한 가격보다 마이너스일 경우 추가 거래를 진행합니다. (분할매수/매도 개발중)

## Installation (설치)

### Repository 복사

```bash
git clone https://github.com/mirae707/coza.git
```

### 모듈 설치

- ccxt 모듈을 사용하므로 ccxt 모듈 설치 및 의존성 파일 설치가 필요합니다.
- 텔레그램 메세지 전송을 위해 텔레그램 모듈 설치가 필요합니다.
- 차트 분석을 위한 pandas와 numpy 가 필요합니다.
- 엑셀파일 자동화를 위한 openpyxl 이 필요합니다.

```bash
pip install ccxt python-telegram-bot numpy openpyxl

# 의존성 문제가 발생하는 경우
sudo apt install build-essential -y # debian / ubuntu
sudo dnf groupinstall "Development Tools" "Development Libraries" # fedora
sudo pacman -S base-devel # arch
```

### 실행모드

- main.py를 실행파일로 권한 부여

```bash
chmod +x ~/coza/main.py
```

### 디렉토리 및 파일 생성

- 로그, 코인 정보, api key 파일을 저장할 directory 생성

```bash
mkdir -p ~/coza/Api
mkdir -p ~/coza/Data
mkdir -p ~/coza/Log
```

- 생성한 directory 안에 사용할 파일 생성
  - 개인 거래소 api key를 입력하세요.
  - 개인 텔레그램 api key와 채팅방 id를 입력하세요.

```bash
cat > ~/coza/Api/api.txt << EOF
public key
secret key
EOF

cat > ~/coza/Api/mybot.txt << EOF
telegram api key
telegram chat id
EOF
```

## 실행 (Run)

### systemctl 사용

- systemctl을 이용하여 자동으로 시작되도록 등록
- User와 Group 란에 자신의 계정 이름을 넣어주세요.

```bash
sudo cat > /etc/systemd/system/trading.service << EOF
[Unit]
Description=Algorithm Trading Bot

[Service]   #user에 본인 계정 입력
Type=simple
WorkingDirectory=/home/user
ExecStart=/home/user/coza/main.py
Restart=on-failure
User=user
Group=user

[Install]
WantedBy=multi-user.target
EOF
```

- systemctl 사용방법

```bash
sudo systemctl start trading.service # 서비스 실행
sudo systemctl status trading.service # 서비스 상태 확인
sudo systemctl stop trading.service # 서비스 정지
sudo systemctl restart trading.service # 서비스 재실행
sudo systemctl enable trading.service # 서비스 자동실행 등록
sudo systemctl disable trading.service # 서비스 자동실행 등록 취소
sudo systemctl daemon-reload # 서비스 변경사항 업데이트
```

### crontab 사용 (개발중)
