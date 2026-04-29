# 🏥 AI Health Report Analyzer

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deployed](https://img.shields.io/badge/Deployed-Streamlit-brightgreen.svg)](https://share.streamlit.io)

> **Upload any health report and get AI-powered insights: What it means, why it happened, how to care, next steps, diet, and exercises.**

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Multi-format Support** | PDF, JPG, PNG, JPEG, TXT files |
| 🔍 **Smart Text Extraction** | PyPDF2 for text PDFs + Tesseract OCR for scanned docs |
| 🩺 **Medical Analysis** | Detects TSH, Cholesterol, BP, Glucose, Hemoglobin, and more |
| 📊 **Health Score** | Visual gauge showing overall health status |
| 💡 **6 Insight Categories** | What it means, Why, How to care, Next steps, Diet, Exercises |
| 🎨 **Clean UI** | Tabbed interface with professional design |
| 🔒 **Privacy First** | No data stored - all processing happens locally |

## 🎯 Medical Conditions Detected

| Condition | Detection Method |
|-----------|------------------|
| Hypothyroidism | TSH > 4.78 |
| Hyperthyroidism | TSH < 0.55 |
| High Cholesterol | Total Cholesterol > 200 |
| Diabetes | Glucose > 126 |
| Prediabetes | Glucose 100-125 |
| Hypertension | BP > 130/80 |
| Anemia | Hemoglobin < 12 |

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Git (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/health-report-analyzer.git
cd health-report-analyzer

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app_complete.py