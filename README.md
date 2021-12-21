# Glitch - FreeType Mutator

- Glitch는 Chrome의 FreeType을 퍼징하는 Mutator입니다.

- CVE-2020-15999 취약점의 루트커즈와 비슷한 이유로 발생할 수 있는 취약점들을 탐지하는 것이 목적입니다.

- 퍼징 테스트 방법

  ```
  # step0 - 필수 설치
  pip3 install pypng
  pip3 install numpy
  
  # step1 - run mutate_server # windows10, ubuntu 공통
  python3 Glitch_server.py
  
  # step2 - Start Fuzzing
  [Windows10]
  python3 run_fuzz_windows10.py --method normal (or --help)
  
  [Ubuntu]
  python3 run_fuzz_ubuntu.py --method normal (or --help)
  ```

- 로그 저장 장소
  - 크래시 로그 : ./log/crash_[날짜 및 시간].log

  - 크래시 html : ./log/crash_freetype_[날짜 및 시간].ttf

## 패치

### 2021-12-22

- git에 업로드

