# Use an official Python runtime as a parent image
FROM python:3.7.4-buster
 
# upgrade pip since some packages (like tensorflow) requires latest pip
RUN pip install --upgrade pip
 
# Set the working directory to /app
WORKDIR /app
 
# Copy the current directory contents into the container at /app
COPY . /app
 
# Install any needed packages specified in requirements.txt
 
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
 
# Make port 80 available to the world outside this container
EXPOSE 80
 
# Define environment variable
ENV NAME World
 
# Run app.py when the container launches
CMD ["python", "apply_pandas.py"]