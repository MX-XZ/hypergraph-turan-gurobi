FROM gurobi/python:11.0.0_3.10

# Set the application directory
WORKDIR /app

# Install additional dependencies
RUN python3 -m pip install numpy itertools

# Copy the application code
ADD ILP.py /app

# Execute the code
CMD ["python", "/app/ILP.py"]