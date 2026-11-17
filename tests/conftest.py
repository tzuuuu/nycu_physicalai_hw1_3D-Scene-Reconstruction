"""在任何測試載入原生數值套件前沿用專案 OpenMP 設定。"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
