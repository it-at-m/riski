FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:f282cb7aad4f01485db1c21ad23166c96391f751d8d025d5c77ba29fb8a57161
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]