FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:c7d56cf78c45ab61406bc2dfebbac562c16e38538393f838991a949577cd3d0a
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]