FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:4ffc1f76c58b4daabcf9da2ba4cd82289d2de8c89830b4420c9d99ff1cac3ae4
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]