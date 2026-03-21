.PHONY: venv setup pipeline bronze silver gold queries agent-api app test lint clean doctor install-ollama

VENV = .venv
OLLAMA_MODEL ?= llama3.2

# Cross-platform detection
ifeq ($(OS),Windows_NT)
    BIN = $(VENV)/Scripts
    PYTHON = python
    RM = rmdir /s /q
    RM_F = del /q
else
    BIN = $(VENV)/bin
    PYTHON = python3
    RM = rm -rf
    RM_F = rm -f
    UNAME_S := $(shell uname -s)
endif

venv:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

install-ollama:
	@command -v ollama >/dev/null 2>&1 && echo "Ollama already installed." || ( \
		echo "Installing Ollama..." && \
		if [ "$(UNAME_S)" = "Linux" ]; then \
			curl -fsSL https://ollama.com/install.sh | sh; \
		elif [ "$(UNAME_S)" = "Darwin" ]; then \
			brew install ollama; \
		else \
			echo "On Windows use: python run.py setup"; exit 1; \
		fi \
	)
	@echo "Ensuring Ollama server is running..."
	@curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 || ( \
		ollama serve >/dev/null 2>&1 & \
		sleep 3 && echo "Ollama server started." \
	)
	@ollama list 2>/dev/null | grep -q "$(OLLAMA_MODEL)" && echo "Model $(OLLAMA_MODEL) already available." || ( \
		echo "Pulling model $(OLLAMA_MODEL)..." && \
		ollama pull $(OLLAMA_MODEL) \
	)

setup: venv install-ollama
	$(BIN)/pip install -r requirements.txt

pipeline:
	PYTHONPATH=$(CURDIR) $(BIN)/python -m pipeline.pipeline run

bronze:
	PYTHONPATH=$(CURDIR) $(BIN)/python -m pipeline.pipeline bronze

silver:
	PYTHONPATH=$(CURDIR) $(BIN)/python -m pipeline.pipeline silver

gold:
	PYTHONPATH=$(CURDIR) $(BIN)/python -m pipeline.pipeline gold

queries:
	PYTHONPATH=$(CURDIR) $(BIN)/python -m pipeline.pipeline queries

agent-api:
	@curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 || ( \
		ollama serve >/dev/null 2>&1 & sleep 3 \
	)
	PYTHONPATH=$(CURDIR) $(BIN)/uvicorn agent.api:app --host 0.0.0.0 --port 8000 --reload

app:
	PYTHONPATH=$(CURDIR) $(BIN)/streamlit run app/main.py

test:
	PYTHONPATH=$(CURDIR) $(BIN)/pytest -v

lint:
	$(BIN)/python -m py_compile pipeline/src/bronze.py
	$(BIN)/python -m py_compile pipeline/src/silver.py
	$(BIN)/python -m py_compile pipeline/src/gold.py
	$(BIN)/python -m py_compile agent/agent.py
	$(BIN)/python -m py_compile agent/llm_backend.py

clean:
	$(RM) pipeline/data/raw pipeline/data/bronze pipeline/data/silver pipeline/data/gold
	$(RM_F) pipeline/data/*.duckdb

doctor:
	$(PYTHON) run.py doctor
