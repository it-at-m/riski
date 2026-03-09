FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:7ae9e7d69002b6af6fa2b22b84d1afa73624bc17c76bf255f45b0ce33e849de9
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]