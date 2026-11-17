"""所有本專案測試在載入原生數值套件前沿用既有 OpenMP 設定。"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
