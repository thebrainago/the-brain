# GPU may nha (do 07/10/2026 22:50) - cho cloud xem ke hoach dung GPU

- GPU: NVIDIA GeForce GT 730, 2 GB VRAM (dong Kepler/Fermi cu, 2014). Driver 471.11 (ban cuoi ho tro dong nay), CUDA toi da 11.4.
- Khong cai: CUDA Toolkit/nvcc, torch, cupy, numba, jax, tensorflow, xgboost, lightgbm, pyopencl.
- Suc manh: ~0,7 TFLOPS FP32, khong co tensor core, bang thong bo nho ~14-28 GB/s. Cung cap 1 CPU Xeon 20 luong con manh hon cho viec nay.
- Han che thuc te: torch/cupy ban moi KHONG ho tro (compute cap thap, can CUDA 11.4 + ban cu); 2 GB VRAM khong du mo hinh lon; khong ho tro FP16 nhanh.
- Ket luan cho ke hoach: GPU nay KHONG dang dung cho backtest/ML. Tester MT5 va quet luoi chay tren CPU. Neu can GPU that: thue cloud GPU (T4/A10...) cho viec nang.
- CPU/RAM de doi chieu: Xeon E5-2630 v4, 10 nhan/20 luong, RAM 32 GB (P11/P12 + C: con ~19,8 GB trong; cache MT5 tren D:).
