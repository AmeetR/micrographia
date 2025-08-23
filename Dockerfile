FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /workspace
COPY . /workspace
RUN pip install --no-cache-dir -e .

CMD ["bash"]

