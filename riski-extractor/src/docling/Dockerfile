FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:dbe515c39b83c10e7c6af38792a440c059baaf660fd62ff00c34c0f5588c7e66
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]