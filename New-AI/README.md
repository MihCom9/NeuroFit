# 🏋️‍♂️ Movement Evaluation AI

A local AI assistant that analyzes and evaluates human movements using 3D coordinate data (X, Y, Z) from a sensor.  
It compares your movement to a reference example and gives feedback using a local LLM (`gemma:2b` via Ollama).

---

## 📌 Features

✅ Compares your movement to a reference with cosine similarity and delta analysis  
✅ Detects which moments your form was off  
✅ Friendly AI feedback powered by a local LLM  
✅ Works offline — no cloud, no internet needed  
✅ Supports real-time Q&A about your performance

---


## ⚙️ Requirements

Make sure the following are installed on your machine:

### 🔹 Python (3.10+)
Install from [https://www.python.org/downloads](https://www.python.org/downloads)

### 🔹 Ollama (for running local AI models)
Install from 👉 [https://ollama.com/download](https://ollama.com/download)

Then, run the following in your terminal:

```bash
ollama pull gemma:2b
```
---
## Used libraries

`pandas, numpy, matplotlib` – for data processing and visualization

`flask` – for the server/backend part

`dtaidistance` – for DTW (Dynamic Time Warping) comparison

`langchain` – for using ChatPromptTemplate (prompt templating for LLMs)

`ollama` – for running the OllamaLLM model locally

---
## 🖥️ Demo Screenshot

![img.png](img.png)
