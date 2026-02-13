FROM python:3.12-slim

WORKDIR /app

# Copy lockfile and install deps first (cache layer)
COPY requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt

# Copy source
COPY . .

# Verify constitution integrity on build
ARG CONSTITUTION_PATH=artifacts/phase-x/constitution/rsa_constitution.v0.1.1.yaml
RUN python -c "from kernel.src.constitution import Constitution; Constitution('${CONSTITUTION_PATH}')"

# Default: run tests
CMD ["python", "-m", "pytest", "tests/test_x0e.py", "-v"]
