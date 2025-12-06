FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:ad9e79e442f02007a38a5ba68820dd1b094b6e23e03e2b777f15acc449239e4d
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]