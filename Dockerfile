# Use a Python base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the .env file
COPY .env .

# Copy the rest of the application code
COPY . .

# Download the local LLM model
# This will be cached by Docker, so it will only be downloaded once
RUN python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; AutoTokenizer.from_pretrained('google/gemma-3-270m-it'); AutoModelForCausalLM.from_pretrained('google/gemma-3-270m-it')"

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI application
# The default is to use the Gemini API
# To use the local LLM, you can override this command when running the container
CMD ["python", "src/api.py"]