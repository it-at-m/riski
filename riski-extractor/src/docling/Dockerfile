FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:a775d1765525029a221a47fda03c91f50960d820ca4853d67b612a5d120ac6fb
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]