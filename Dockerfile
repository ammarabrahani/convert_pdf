# Use the AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies (including Poppler)
RUN yum install -y poppler-utils && yum clean all

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Copy the application code
COPY main.py ./

# Set the CMD to your handler
CMD ["main.handler"]