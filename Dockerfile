FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
ARG PYTORCH_CUDA_VER=cu121
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY . /workspace
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/${PYTORCH_CUDA_VER} \
    && pip install --no-cache-dir -e .[finetune]
CMD ["bash"]
