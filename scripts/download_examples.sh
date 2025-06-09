#!/usr/bin/env bash
# Download example PDF files into pdf/ directory
set -e

mkdir -p pdf
cd pdf

urls=(
  "https://arxiv.org/pdf/1706.03762.pdf" # Attention Is All You Need
  "https://arxiv.org/pdf/1512.03385.pdf" # Deep Residual Learning
  "https://arxiv.org/pdf/1810.04805.pdf" # BERT
  "https://arxiv.org/pdf/2005.14165.pdf" # GPT-3
  "https://arxiv.org/pdf/1412.6980.pdf"  # Adam Optimizer
  "https://arxiv.org/pdf/1406.2661.pdf"  # GANs
  "https://arxiv.org/pdf/1505.04597.pdf" # U-Net
)

for url in "${urls[@]}"; do
  fname="$(basename "$url")"
  wget -nc "$url" -O "$fname"
done
