FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:630815bf3d9a19d50df9caade6f396f60a13b73056d8422ad042de8ca33cb788
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]