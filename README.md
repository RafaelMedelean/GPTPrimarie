
# qwen-embeddings

## Prerequisites

- **NVIDIA GPU:** 
    This project requires a PC with one NVIDIA GPU. 
    Ensure that you have the latest NVIDIA drivers and CUDA Toolkit installed.

    - Cuda(nvcc): [12.8](https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=Ubuntu&target_version=22.04&target_type=deb_local)

- **Conda or Python:** 
    - Python version: 3.10.16
    - Conda version: 24.3.0
    - You can either use Conda (Anaconda/Miniconda) to manage your environments.

## Installation

### Using Conda

1. **Install Conda:**
   - Download and install 

2. **Create and Activate the Environment:**
   - conda create -n qwen-env python=3.10 -y
   - conda activate qwen-env

3. **Run the feedback platform:**

    **Frontend:** 

    cd frontend
    npm run dev - port 5173

    **Backend:**

    cd chat_backend
    python main.py - port 8000

